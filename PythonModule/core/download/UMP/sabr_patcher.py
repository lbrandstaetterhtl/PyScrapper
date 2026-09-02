from __future__ import annotations

"""
Stateful YouTube SABR/UMP POST-body patcher.

Design goals
------------
* Start from a real browser/player SABR request body.
* Preserve every unknown protobuf field byte-for-byte where possible.
* Learn playbackCookie, media segment ranges and SABR contexts from UMP responses.
* Update only fields whose semantics are reasonably established.
* Optionally pin the first selected audio/video itags so the codec/representation
  stays stable instead of following the browser's adaptive video switch.

This module intentionally does NOT generate/bypass YouTube proof-of-origin tokens.
A valid token already present in the request is preserved; a refreshed valid token
can be supplied with ``set_po_token``.

No generated protobuf classes are required; this is a small wire-format parser so
it can be dropped directly into the existing UMP package.
"""

from dataclasses import dataclass, field
import struct
import time
from typing import Iterable, Iterator


# ---------------------------------------------------------------------------
# Protobuf wire helpers
# ---------------------------------------------------------------------------

ProtoField = list  # [field_number: int, wire_type: int, value: int|bytes]


def _read_proto_varint(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if pos >= len(data):
            raise ValueError("Unexpected EOF while reading protobuf varint")
        b = data[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            return value, pos
        shift += 7
        if shift >= 70:
            raise ValueError("Invalid protobuf varint")


def _write_proto_varint(value: int) -> bytes:
    if value < 0:
        # protobuf int64 negative values are ten-byte two's complement varints.
        value &= (1 << 64) - 1
    out = bytearray()
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def parse_proto(data: bytes) -> list[ProtoField]:
    fields: list[ProtoField] = []
    pos = 0
    while pos < len(data):
        key, pos = _read_proto_varint(data, pos)
        number = key >> 3
        wire = key & 7
        if number == 0:
            raise ValueError("Invalid protobuf field number 0")

        if wire == 0:
            value, pos = _read_proto_varint(data, pos)
        elif wire == 1:
            if pos + 8 > len(data):
                raise ValueError("Unexpected EOF in protobuf fixed64")
            value = data[pos:pos + 8]
            pos += 8
        elif wire == 2:
            size, pos = _read_proto_varint(data, pos)
            end = pos + size
            if end > len(data):
                raise ValueError("Unexpected EOF in protobuf bytes field")
            value = data[pos:end]
            pos = end
        elif wire == 5:
            if pos + 4 > len(data):
                raise ValueError("Unexpected EOF in protobuf fixed32")
            value = data[pos:pos + 4]
            pos += 4
        else:
            raise ValueError(f"Unsupported protobuf wire type {wire}")

        fields.append([number, wire, value])
    return fields


def encode_proto(fields: Iterable[ProtoField]) -> bytes:
    out = bytearray()
    for number, wire, value in fields:
        out += _write_proto_varint((int(number) << 3) | int(wire))
        if wire == 0:
            out += _write_proto_varint(int(value))
        elif wire == 2:
            raw = bytes(value)
            out += _write_proto_varint(len(raw))
            out += raw
        elif wire in (1, 5):
            out += bytes(value)
        else:
            raise ValueError(f"Unsupported protobuf wire type {wire}")
    return bytes(out)


def _clone_fields(fields: Iterable[ProtoField]) -> list[ProtoField]:
    return [[n, w, bytes(v) if isinstance(v, (bytes, bytearray)) else v] for n, w, v in fields]


def _first(fields: Iterable[ProtoField], number: int, wire: int | None = None) -> ProtoField | None:
    for f in fields:
        if f[0] == number and (wire is None or f[1] == wire):
            return f
    return None


def _all(fields: Iterable[ProtoField], number: int, wire: int | None = None) -> list[ProtoField]:
    return [f for f in fields if f[0] == number and (wire is None or f[1] == wire)]


def _uint(fields: Iterable[ProtoField], number: int, default: int | None = None) -> int | None:
    f = _first(fields, number, 0)
    return int(f[2]) if f is not None else default


def _bytes(fields: Iterable[ProtoField], number: int, default: bytes | None = None) -> bytes | None:
    f = _first(fields, number, 2)
    return bytes(f[2]) if f is not None else default


def _set_uint(fields: list[ProtoField], number: int, value: int, *, create: bool = False) -> bool:
    f = _first(fields, number, 0)
    if f is not None:
        f[2] = max(0, int(value))
        return True
    if create:
        fields.append([number, 0, max(0, int(value))])
        return True
    return False


def _replace_bytes_field(fields: list[ProtoField], number: int, value: bytes, *, create: bool = True) -> None:
    f = _first(fields, number, 2)
    if f is not None:
        f[2] = bytes(value)
    elif create:
        fields.append([number, 2, bytes(value)])


# ---------------------------------------------------------------------------
# UMP framing
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class UMPPart:
    part_type: int
    payload: bytes


def read_ump_varint(data: bytes, pos: int) -> tuple[int, int]:
    """Read YouTube UMP's prefix varint (not protobuf LEB128)."""
    if pos >= len(data):
        raise ValueError("Unexpected EOF while reading UMP varint")

    first = data[pos]
    if first < 0x80:
        length = 1
    elif first < 0xC0:
        length = 2
    elif first < 0xE0:
        length = 3
    elif first < 0xF0:
        length = 4
    else:
        length = 5

    end = pos + length
    if end > len(data):
        raise ValueError("Unexpected EOF inside UMP varint")

    if length == 1:
        value = first
    elif length == 2:
        value = (data[pos] & 0x3F) + 64 * data[pos + 1]
    elif length == 3:
        value = (data[pos] & 0x1F) + 32 * (data[pos + 1] + 256 * data[pos + 2])
    elif length == 4:
        value = (data[pos] & 0x0F) + 16 * (
            data[pos + 1] + 256 * (data[pos + 2] + 256 * data[pos + 3])
        )
    else:
        value = int.from_bytes(data[pos + 1:pos + 5], "little", signed=False)

    return value, end


def parse_ump(data: bytes) -> list[UMPPart]:
    parts: list[UMPPart] = []
    pos = 0
    while pos < len(data):
        part_type, pos = read_ump_varint(data, pos)
        size, pos = read_ump_varint(data, pos)
        end = pos + size
        if end > len(data):
            raise ValueError(
                f"UMP part exceeds response: type={part_type}, size={size}, "
                f"remaining={len(data) - pos}"
            )
        parts.append(UMPPart(part_type, data[pos:end]))
        pos = end
    return parts


# UMP part IDs seen in the supplied capture / current protocol implementations.
UMP_MEDIA_HEADER = 20
UMP_MEDIA = 21
UMP_MEDIA_END = 22
UMP_NEXT_REQUEST_POLICY = 35
UMP_SABR_CONTEXT_UPDATE = 57
UMP_SABR_CONTEXT_SENDING_POLICY = 59


# ---------------------------------------------------------------------------
# SABR structures
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class FormatId:
    raw: bytes
    itag: int | None
    lmt: int | None = None

    @classmethod
    def from_raw(cls, raw: bytes) -> "FormatId":
        try:
            f = parse_proto(raw)
        except ValueError:
            return cls(bytes(raw), None, None)
        return cls(bytes(raw), _uint(f, 1), _uint(f, 2))


@dataclass(slots=True)
class SegmentInfo:
    sequence: int
    start_ms: int
    duration_ms: int

    @property
    def end_ms(self) -> int:
        return self.start_ms + self.duration_ms


@dataclass(slots=True)
class TrackState:
    format_id: FormatId
    header_id: int | None = None
    segments: dict[int, SegmentInfo] = field(default_factory=dict)
    initialized: bool = False
    first_seen_order: int = 0

    def add_segment(self, segment: SegmentInfo) -> None:
        self.segments[segment.sequence] = segment

    def contiguous_envelope(self) -> tuple[int, int, int, int] | None:
        """Return start, duration, first seq, last seq for the contiguous run.

        SABR bufferedRanges describe actually received segments. If a response is
        lost or a sequence gap appears, advertising across that hole is unsafe, so
        we keep only the longest contiguous run. Ties prefer the earlier run.
        """
        if not self.segments:
            return None

        seqs = sorted(self.segments)
        runs: list[list[int]] = []
        run = [seqs[0]]
        for seq in seqs[1:]:
            if seq == run[-1] + 1:
                run.append(seq)
            else:
                runs.append(run)
                run = [seq]
        runs.append(run)
        best = max(runs, key=lambda r: (len(r), -r[0]))
        infos = [self.segments[s] for s in best]
        start = min(x.start_ms for x in infos)
        end = max(x.end_ms for x in infos)
        return start, max(0, end - start), best[0], best[-1]


@dataclass(slots=True)
class NextRequestPolicy:
    target_audio_readahead_ms: int | None = None
    target_video_readahead_ms: int | None = None
    max_time_since_last_request_ms: int | None = None
    backoff_time_ms: int = 0
    playback_cookie: bytes | None = None
    video_id: str | None = None


@dataclass(slots=True)
class MediaChunk:
    header_id: int
    itag: int | None
    data: bytes


class SABRRequestPatcher:
    """Stateful patcher for successive VideoPlaybackAbrRequest bodies.

    Typical use::

        patcher = SABRRequestPatcher(initial_body, lock_itags=True)
        body = initial_body

        while True:
            t0 = time.monotonic()
            response = post(body)
            transfer_ms = (time.monotonic() - t0) * 1000

            patcher.observe_response(response, transfer_ms=transfer_ms)
            body = patcher.build_next_request(player_time_ms=current_player_ms)

    ``lock_itags=True`` pins the first selected audio and video representations.
    This is useful when you want stable codecs/containers rather than browser ABR.
    """

    def __init__(
        self,
        initial_body: bytes,
        *,
        lock_itags: bool = True,
        audio_itag: int | None = None,
        video_itag: int | None = None,
        update_bandwidth_estimate: bool = True,
        bandwidth_alpha: float = 0.25,
    ):
        self.initial_body = bytes(initial_body)
        self._template = parse_proto(initial_body)
        self.lock_itags = bool(lock_itags)
        self.locked_audio_itag = audio_itag
        self.locked_video_itag = video_itag
        self.update_bandwidth_estimate = update_bandwidth_estimate
        self.bandwidth_alpha = max(0.0, min(1.0, float(bandwidth_alpha)))

        self._started = time.monotonic()
        self._last_action = self._started
        self._last_request_built = self._started

        self._client_template: list[ProtoField] | None = None
        self._streamer_template: list[ProtoField] | None = None
        self._client_initial: dict[int, int] = {}
        self._po_token: bytes | None = None
        self._playback_cookie: bytes | None = None
        self.next_policy = NextRequestPolicy()
        self._bandwidth_estimate: float | None = None

        self.preferred_audio: list[FormatId] = []
        self.preferred_video: list[FormatId] = []
        self._preferred_audio_by_itag: dict[int, FormatId] = {}
        self._preferred_video_by_itag: dict[int, FormatId] = {}
        self._known_formats: dict[int, FormatId] = {}
        self._tracks: dict[int, TrackState] = {}
        self._header_to_itag: dict[int, int] = {}
        self._selected_itags: list[int] = []
        self._seen_counter = 0

        # SABR context state. Unknown context bytes are opaque and preserved.
        self._sabr_context_values: dict[int, bytes] = {}
        self._active_sabr_contexts: set[int] = set()

        self._read_initial_request()

    # ------------------------------------------------------------------
    # Public state
    # ------------------------------------------------------------------

    @property
    def playback_cookie(self) -> bytes | None:
        return self._playback_cookie

    @property
    def po_token(self) -> bytes | None:
        return self._po_token

    @property
    def selected_itags(self) -> tuple[int, ...]:
        return tuple(self._selected_itags)

    @property
    def tracks(self) -> dict[int, TrackState]:
        return self._tracks

    @property
    def next_delay_ms(self) -> int:
        return max(0, int(self.next_policy.backoff_time_ms or 0))

    def set_po_token(self, token: bytes | None) -> None:
        """Install a valid externally obtained proof-of-origin token.

        The patcher does not mint or bypass these tokens. Passing ``None`` keeps
        the existing token untouched; pass ``b''`` only if you deliberately want
        the field to contain an empty token.
        """
        if token is not None:
            self._po_token = bytes(token)

    def mark_action(self) -> None:
        """Reset ClientAbrState.timeSinceLastActionMs (field 39)."""
        self._last_action = time.monotonic()

    # ------------------------------------------------------------------
    # Request parsing/building
    # ------------------------------------------------------------------

    def _read_initial_request(self) -> None:
        state_f = _first(self._template, 1, 2)
        if state_f is not None:
            self._client_template = parse_proto(state_f[2])
            for n in (23, 28, 29, 36, 39):
                v = _uint(self._client_template, n)
                if v is not None:
                    self._client_initial[n] = v
            bw = self._client_initial.get(23)
            if bw is not None:
                self._bandwidth_estimate = float(bw)

        self.preferred_audio = [FormatId.from_raw(f[2]) for f in _all(self._template, 16, 2)]
        self.preferred_video = [FormatId.from_raw(f[2]) for f in _all(self._template, 17, 2)]

        for fmt in self.preferred_audio:
            if fmt.itag is not None:
                self._preferred_audio_by_itag[fmt.itag] = fmt
                self._known_formats.setdefault(fmt.itag, fmt)
        for fmt in self.preferred_video:
            if fmt.itag is not None:
                self._preferred_video_by_itag[fmt.itag] = fmt
                self._known_formats.setdefault(fmt.itag, fmt)

        for f in _all(self._template, 2, 2):
            fmt = FormatId.from_raw(f[2])
            if fmt.itag is not None:
                self._remember_selected(fmt)

        streamer_f = _first(self._template, 19, 2)
        if streamer_f is not None:
            self._streamer_template = parse_proto(streamer_f[2])
            self._po_token = _bytes(self._streamer_template, 2)
            self._playback_cookie = _bytes(self._streamer_template, 3)
            self._read_initial_sabr_contexts(self._streamer_template)

        if self.lock_itags:
            # If caller supplied explicit locks, validate that their FormatId is
            # already known. Otherwise first response/selection will pin them.
            self._validate_explicit_lock(self.locked_audio_itag, audio=True)
            self._validate_explicit_lock(self.locked_video_itag, audio=False)

    def _validate_explicit_lock(self, itag: int | None, *, audio: bool) -> None:
        if itag is None:
            return
        table = self._preferred_audio_by_itag if audio else self._preferred_video_by_itag
        if itag not in table and itag not in self._known_formats:
            kind = "audio" if audio else "video"
            raise ValueError(f"Requested locked {kind} itag {itag} is not present in initial SABR body")

    def _read_initial_sabr_contexts(self, streamer: list[ProtoField]) -> None:
        for f in _all(streamer, 5, 2):
            try:
                ctx = parse_proto(f[2])
            except ValueError:
                continue
            typ = _uint(ctx, 1)
            val = _bytes(ctx, 2)
            if typ is not None and val is not None:
                self._sabr_context_values[typ] = val
                self._active_sabr_contexts.add(typ)

        # Field 6 is a packed list of known-but-currently-unsent context types.
        for f in _all(streamer, 6, 2):
            try:
                pos = 0
                raw = bytes(f[2])
                while pos < len(raw):
                    typ, pos = _read_proto_varint(raw, pos)
                    self._active_sabr_contexts.discard(typ)
            except ValueError:
                pass

    def _remember_selected(self, fmt: FormatId) -> None:
        if fmt.itag is None:
            return
        self._known_formats[fmt.itag] = fmt
        if fmt.itag not in self._selected_itags:
            self._selected_itags.append(fmt.itag)
        self._pin_if_needed(fmt.itag)

    def _pin_if_needed(self, itag: int) -> None:
        if not self.lock_itags:
            return
        if itag in self._preferred_audio_by_itag and self.locked_audio_itag is None:
            self.locked_audio_itag = itag
        if itag in self._preferred_video_by_itag and self.locked_video_itag is None:
            self.locked_video_itag = itag

    def build_next_request(
        self,
        *,
        player_time_ms: int | None = None,
        time_since_last_seek_ms: int | None = None,
        elapsed_wall_time_ms: int | None = None,
        time_since_last_action_ms: int | None = None,
        po_token: bytes | None = None,
    ) -> bytes:
        """Build the next browser-like VideoPlaybackAbrRequest body.

        ``player_time_ms`` should be the actual media clock when you have one.
        For a non-playing downloader it defaults to realtime elapsed since the
        patcher was created, which mimics uninterrupted playback.

        Timing fields are intentionally independent:
          field 28 = player time
          field 29 = time since last seek
          field 36 = elapsed wall time
          field 39 = time since last player action
        """
        now = time.monotonic()
        elapsed = max(0, int((now - self._started) * 1000))

        if po_token is not None:
            self.set_po_token(po_token)

        fields = _clone_fields(self._template)

        # ----- field 1: ClientAbrState ---------------------------------
        state_f = _first(fields, 1, 2)
        if state_f is not None:
            state = parse_proto(state_f[2])

            base_player = self._client_initial.get(28, 0)
            base_seek = self._client_initial.get(29, 0)
            base_wall = self._client_initial.get(36, 0)
            base_action = self._client_initial.get(39, 0)

            if player_time_ms is None:
                player_time_ms = base_player + elapsed
            if time_since_last_seek_ms is None:
                time_since_last_seek_ms = base_seek + elapsed
            if elapsed_wall_time_ms is None:
                elapsed_wall_time_ms = base_wall + elapsed
            if time_since_last_action_ms is None:
                time_since_last_action_ms = base_action + max(0, int((now - self._last_action) * 1000))

            # Only create field28 if missing; the other timing fields are updated
            # only when the original browser body already contained them.
            _set_uint(state, 28, player_time_ms, create=True)
            _set_uint(state, 29, time_since_last_seek_ms, create=False)
            _set_uint(state, 36, elapsed_wall_time_ms, create=False)
            _set_uint(state, 39, time_since_last_action_ms, create=False)

            if self.update_bandwidth_estimate and self._bandwidth_estimate is not None:
                _set_uint(state, 23, round(self._bandwidth_estimate), create=False)

            state_f[2] = encode_proto(state)

        # ----- fields 2/3: selected formats + cumulative buffered ranges -
        fields = [f for f in fields if f[0] not in (2, 3)]
        selected = self._formats_for_next_request()
        selected_fields = [[2, 2, fmt.raw] for fmt in selected]

        range_fields: list[ProtoField] = []
        for fmt in selected:
            if fmt.itag is None:
                continue
            track = self._tracks.get(fmt.itag)
            if track is None:
                continue
            envelope = track.contiguous_envelope()
            if envelope is None:
                continue
            start_ms, duration_ms, first_seq, last_seq = envelope
            range_body = encode_proto([
                [1, 2, fmt.raw],
                [2, 0, start_ms],
                [3, 0, duration_ms],
                [4, 0, first_seq],
                [5, 0, last_seq],
            ])
            range_fields.append([3, 2, range_body])

        # Browser ordering in the supplied capture is field1, field2*, field3*,
        # then field5/16/17/19. Insert after the first field1 when possible.
        insert_at = 0
        for i, f in enumerate(fields):
            if f[0] == 1:
                insert_at = i + 1
                break
        fields[insert_at:insert_at] = selected_fields + range_fields

        # ----- fields 16/17: preferred formats --------------------------
        if self.lock_itags:
            fields = self._apply_locked_preferences(fields)

        # ----- field 19: StreamerContext -------------------------------
        streamer_f = _first(fields, 19, 2)
        if streamer_f is not None:
            streamer = parse_proto(streamer_f[2])
            if self._po_token is not None:
                _replace_bytes_field(streamer, 2, self._po_token, create=True)
            if self._playback_cookie is not None:
                _replace_bytes_field(streamer, 3, self._playback_cookie, create=True)
            streamer = self._apply_sabr_contexts(streamer)
            streamer_f[2] = encode_proto(streamer)

        self._last_request_built = now
        return encode_proto(fields)

    def _formats_for_next_request(self) -> list[FormatId]:
        if self.lock_itags:
            out: list[FormatId] = []
            for itag in (self.locked_audio_itag, self.locked_video_itag):
                if itag is None:
                    continue
                fmt = self._known_formats.get(itag)
                if fmt is not None:
                    out.append(fmt)
            # Before the first response there may not be a selected pair yet.
            # Do not invent one; initial request should normally be sent unchanged.
            return out

        out = []
        for itag in self._selected_itags:
            fmt = self._known_formats.get(itag)
            if fmt is not None:
                out.append(fmt)
        return out

    def _apply_locked_preferences(self, fields: list[ProtoField]) -> list[ProtoField]:
        replacement_audio: list[ProtoField] = []
        replacement_video: list[ProtoField] = []

        if self.locked_audio_itag is not None:
            fmt = self._known_formats.get(self.locked_audio_itag) or self._preferred_audio_by_itag.get(self.locked_audio_itag)
            if fmt is not None:
                replacement_audio = [[16, 2, fmt.raw]]

        if self.locked_video_itag is not None:
            fmt = self._known_formats.get(self.locked_video_itag) or self._preferred_video_by_itag.get(self.locked_video_itag)
            if fmt is not None:
                replacement_video = [[17, 2, fmt.raw]]

        if not replacement_audio and not replacement_video:
            return fields

        result: list[ProtoField] = []
        inserted_audio = False
        inserted_video = False
        for f in fields:
            if f[0] == 16:
                if not inserted_audio and replacement_audio:
                    result.extend(replacement_audio)
                    inserted_audio = True
                elif not replacement_audio:
                    result.append(f)
                continue
            if f[0] == 17:
                if not inserted_video and replacement_video:
                    result.extend(replacement_video)
                    inserted_video = True
                elif not replacement_video:
                    result.append(f)
                continue
            result.append(f)

        # Initial bodies normally have both fields, but make insertion robust.
        if replacement_audio and not inserted_audio:
            result.extend(replacement_audio)
        if replacement_video and not inserted_video:
            result.extend(replacement_video)
        return result

    def _apply_sabr_contexts(self, streamer: list[ProtoField]) -> list[ProtoField]:
        # Replace only context fields 5/6; preserve every other opaque field.
        streamer = [f for f in streamer if f[0] not in (5, 6)]

        for typ in sorted(self._active_sabr_contexts):
            value = self._sabr_context_values.get(typ)
            if value is None:
                continue
            ctx = encode_proto([[1, 0, typ], [2, 2, value]])
            streamer.append([5, 2, ctx])

        inactive = sorted(set(self._sabr_context_values) - self._active_sabr_contexts)
        if inactive:
            packed = b"".join(_write_proto_varint(x) for x in inactive)
            streamer.append([6, 2, packed])
        return streamer

    # ------------------------------------------------------------------
    # Response observation
    # ------------------------------------------------------------------

    def observe_response(self, data: bytes, *, transfer_ms: float | None = None) -> list[UMPPart]:
        """Consume a UMP response and update state for the next request."""
        parts = parse_ump(data)

        if transfer_ms is not None and transfer_ms > 0 and len(data) > 0:
            # bits/s. Keep the browser's current estimate as the seed and smooth
            # measurements so one tiny control response does not collapse it.
            sample_bps = len(data) * 8.0 * 1000.0 / transfer_ms
            if self._bandwidth_estimate is None:
                self._bandwidth_estimate = sample_bps
            else:
                a = self.bandwidth_alpha
                self._bandwidth_estimate = (1.0 - a) * self._bandwidth_estimate + a * sample_bps

        for part in parts:
            if part.part_type == UMP_MEDIA_HEADER:
                self._observe_media_header(part.payload)
            elif part.part_type == UMP_NEXT_REQUEST_POLICY:
                self._observe_next_request_policy(part.payload)
            elif part.part_type == UMP_SABR_CONTEXT_UPDATE:
                self._observe_sabr_context_update(part.payload)
            elif part.part_type == UMP_SABR_CONTEXT_SENDING_POLICY:
                self._observe_sabr_context_sending_policy(part.payload)

        return parts

    def _observe_media_header(self, payload: bytes) -> None:
        try:
            h = parse_proto(payload)
        except ValueError:
            return

        header_id = _uint(h, 1)
        itag = _uint(h, 3)
        is_init = bool(_uint(h, 8, 0))
        sequence = _uint(h, 9)
        start_ms = _uint(h, 11)
        duration_ms = _uint(h, 12)
        format_raw = _bytes(h, 13)

        fmt: FormatId | None = None
        if format_raw is not None:
            fmt = FormatId.from_raw(format_raw)
            if fmt.itag is not None:
                itag = fmt.itag
                self._known_formats[itag] = fmt
        if itag is None:
            return

        if fmt is None:
            fmt = self._known_formats.get(itag)
        if fmt is None:
            # We need the full FormatId (itag + lmt/etc.) for request ranges. Try
            # the preferred representation before falling back to itag-only.
            fmt = self._preferred_audio_by_itag.get(itag) or self._preferred_video_by_itag.get(itag)
        if fmt is None:
            fmt = FormatId(encode_proto([[1, 0, itag]]), itag, None)
            self._known_formats[itag] = fmt

        track = self._tracks.get(itag)
        if track is None:
            self._seen_counter += 1
            track = TrackState(fmt, first_seen_order=self._seen_counter)
            self._tracks[itag] = track
        else:
            track.format_id = fmt

        if header_id is not None:
            track.header_id = header_id
            self._header_to_itag[header_id] = itag

        if is_init:
            track.initialized = True
            self._remember_selected(fmt)

        if sequence is not None and start_ms is not None and duration_ms is not None:
            track.add_segment(SegmentInfo(sequence, start_ms, duration_ms))
            self._remember_selected(fmt)

    def _observe_next_request_policy(self, payload: bytes) -> None:
        try:
            p = parse_proto(payload)
        except ValueError:
            return

        cookie = _bytes(p, 7)
        video_id_raw = _bytes(p, 8)
        video_id = None
        if video_id_raw is not None:
            try:
                video_id = video_id_raw.decode("utf-8")
            except UnicodeDecodeError:
                video_id = None

        self.next_policy = NextRequestPolicy(
            target_audio_readahead_ms=_uint(p, 1),
            target_video_readahead_ms=_uint(p, 2),
            max_time_since_last_request_ms=_uint(p, 3),
            backoff_time_ms=_uint(p, 4, 0) or 0,
            playback_cookie=cookie,
            video_id=video_id,
        )
        if cookie is not None:
            # This is the critical response -> next-request state transition.
            self._playback_cookie = cookie

    def _observe_sabr_context_update(self, payload: bytes) -> None:
        try:
            u = parse_proto(payload)
        except ValueError:
            return
        typ = _uint(u, 1)
        value = _bytes(u, 3)
        send_by_default = bool(_uint(u, 4, 0))
        if typ is None or value is None:
            return
        self._sabr_context_values[typ] = value
        if send_by_default:
            self._active_sabr_contexts.add(typ)

    def _observe_sabr_context_sending_policy(self, payload: bytes) -> None:
        try:
            p = parse_proto(payload)
        except ValueError:
            return

        starts = self._decode_repeated_uints(p, 1)
        stops = self._decode_repeated_uints(p, 2)
        discards = self._decode_repeated_uints(p, 3)
        self._active_sabr_contexts.update(starts)
        self._active_sabr_contexts.difference_update(stops)
        for typ in discards:
            self._active_sabr_contexts.discard(typ)
            self._sabr_context_values.pop(typ, None)

    @staticmethod
    def _decode_repeated_uints(fields: list[ProtoField], number: int) -> set[int]:
        out: set[int] = set()
        for f in fields:
            if f[0] != number:
                continue
            if f[1] == 0:
                out.add(int(f[2]))
            elif f[1] == 2:
                raw = bytes(f[2])
                pos = 0
                try:
                    while pos < len(raw):
                        value, pos = _read_proto_varint(raw, pos)
                        out.add(value)
                except ValueError:
                    pass
        return out

    # ------------------------------------------------------------------
    # UMP media extraction helpers
    # ------------------------------------------------------------------

    def iter_media_chunks(self, data: bytes) -> Iterator[MediaChunk]:
        """Yield MEDIA payloads with their UMP header id and resolved itag.

        Unlike the old ``payload[0]`` implementation, UMP header IDs are decoded
        with the UMP varint format and therefore are not assumed to fit one byte.
        """
        for part in parse_ump(data):
            if part.part_type != UMP_MEDIA or not part.payload:
                continue
            try:
                header_id, pos = read_ump_varint(part.payload, 0)
            except ValueError:
                continue
            yield MediaChunk(header_id, self._header_to_itag.get(header_id), part.payload[pos:])

    def media_by_itag(self, data: bytes) -> dict[int | None, bytes]:
        out: dict[int | None, bytearray] = {}
        for chunk in self.iter_media_chunks(data):
            out.setdefault(chunk.itag, bytearray()).extend(chunk.data)
        return {itag: bytes(buf) for itag, buf in out.items()}

    # ------------------------------------------------------------------
    # Debug helpers
    # ------------------------------------------------------------------

    def debug_state(self) -> dict:
        return {
            "selected_itags": list(self._selected_itags),
            "locked_audio_itag": self.locked_audio_itag,
            "locked_video_itag": self.locked_video_itag,
            "playback_cookie_len": len(self._playback_cookie) if self._playback_cookie is not None else None,
            "po_token_len": len(self._po_token) if self._po_token is not None else None,
            "bandwidth_estimate": round(self._bandwidth_estimate) if self._bandwidth_estimate is not None else None,
            "next_backoff_ms": self.next_delay_ms,
            "ranges": {
                itag: track.contiguous_envelope()
                for itag, track in sorted(self._tracks.items())
                if track.contiguous_envelope() is not None
            },
            "active_sabr_contexts": sorted(self._active_sabr_contexts),
        }
