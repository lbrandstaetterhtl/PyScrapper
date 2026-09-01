from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping

import socket
from urllib import error as urllib_error
from urllib import request as urllib_request

MODES = ("quick", "normal", "intense")


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "mode",
        nargs="?",
        choices=MODES,
        help="Testtiefe: quick, normal oder intense (Default: normal)",
    )
    parser.add_argument(
        "--mode",
        dest="mode_flag",
        choices=MODES,
        help="Alternative Schreibweise fuer den Testmodus",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8765",
        help="Basis-URL des Servers (Default: http://127.0.0.1:8765)",
    )


def selected_mode(args: argparse.Namespace) -> str:
    return args.mode_flag or args.mode or "normal"


def mode_at_least(mode: str, required: str) -> bool:
    rank = {"quick": 0, "normal": 1, "intense": 2}
    return rank[mode] >= rank[required]


def load_env_value(env_file: Path, key: str) -> str | None:
    try:
        from dotenv import dotenv_values

        values = dotenv_values(env_file)
        value = values.get(key)
        if value:
            return str(value)
    except ImportError:
        pass

    if not env_file.exists():
        return None

    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        current_key, _, value = line.partition("=")
        if current_key.strip() == key:
            return value.strip().strip('"').strip("'")
    return None


def mask_secret(value: str) -> str:
    if len(value) <= 5:
        return "***"
    return f"{value[:3]}***{value[-2:]}"


def compact_json(value: Any, limit: int = 340) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        text = repr(value)
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... <{len(text) - limit} chars omitted>"


def response_preview(response: "HttpResponse", limit: int = 500) -> str:
    text = response.text.replace("\r", "\\r").replace("\n", "\\n")
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... <{len(text) - limit} chars omitted>"


@dataclass(slots=True)
class TestOutcome:
    state: str  # PASS / FAIL / NOTE
    reason: str


class Reporter:
    def __init__(self, suite: str, mode: str, base_url: str, log_file: Path):
        self.suite = suite
        self.mode = mode
        self.base_url = base_url.rstrip("/")
        self.log_file = log_file
        self.started = time.perf_counter()
        self.index = 0
        self.passed = 0
        self.failed = 0
        self.noted = 0
        self.log_file.write_text(
            f"{suite} | mode={mode} | started={datetime.now().isoformat()}\n",
            encoding="utf-8",
        )

    def log(self, message: str = "") -> None:
        line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
        print(line)
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def banner(self, target: str, script: Path, env_file: Path) -> None:
        self.log("=" * 88)
        self.log(f"SUITE      : {self.suite}")
        self.log(f"MODE       : {self.mode}")
        self.log(f"TARGET     : {target}")
        self.log(f"SCRIPT     : {script.resolve()}")
        self.log(f"ENV        : {env_file.resolve()}")
        self.log(f"LOG        : {self.log_file.resolve()}")
        self.log("=" * 88)

    def section(self, title: str) -> None:
        self.log("")
        self.log(f"--- {title} " + "-" * max(1, 78 - len(title)))

    def record(
        self,
        *,
        name: str,
        method: str,
        url: str,
        expectation: str,
        headers: Mapping[str, str],
        request_body: Any,
        outcome: TestOutcome,
        elapsed: float,
        response: "HttpResponse" | None = None,
        error: Exception | None = None,
        header_name: str = "X-Admin-Key",
    ) -> str:
        self.index += 1
        state = outcome.state
        if state == "PASS":
            self.passed += 1
        elif state == "FAIL":
            self.failed += 1
        else:
            self.noted += 1

        actual = f"HTTP {response.status_code}" if response is not None else type(error).__name__ if error else "no response"
        self.log(
            f"[{state:<4}] #{self.index:03d} {name} | {method} {url} | "
            f"expected={expectation} | actual={actual} | {elapsed:.3f}s"
        )
        self.log(f"       reason : {outcome.reason}")
        self.log(f"       auth   : {header_name}={'set' if header_name in headers else 'missing'}")
        if request_body is not None:
            self.log(f"       request: {compact_json(request_body)}")
        if response is not None:
            content_type = response.headers.get("content-type", "<none>")
            self.log(f"       type   : {content_type}")
            self.log(f"       body   : {response_preview(response)}")
        if error is not None:
            self.log(f"       error  : {type(error).__name__}: {error}")
        return state

    def summary(self) -> int:
        elapsed = time.perf_counter() - self.started
        total = self.passed + self.failed + self.noted
        self.log("")
        self.log("=" * 88)
        self.log(
            f"SUMMARY | mode={self.mode} | total={total} | PASS={self.passed} | "
            f"FAIL={self.failed} | NOTE={self.noted} | duration={elapsed:.2f}s"
        )
        if self.failed:
            self.log("RESULT  | FAILED - mindestens ein Test ist auffaellig.")
        else:
            self.log("RESULT  | OK - kein bewerteter Test ist fehlgeschlagen.")
        self.log(f"LOG     | {self.log_file.resolve()}")
        self.log("=" * 88)
        return 0 if self.failed == 0 else 1


@dataclass(slots=True)
class HttpResponse:
    status_code: int
    text: str
    headers: Mapping[str, str]


def _decode_body(raw: bytes, headers: Mapping[str, str]) -> str:
    content_type = headers.get("content-type", "")
    charset = "utf-8"
    for part in content_type.split(";")[1:]:
        key, sep, value = part.strip().partition("=")
        if sep and key.lower() == "charset" and value.strip():
            charset = value.strip().strip('"')
            break
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def _urllib_request(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: Any,
    timeout: float,
) -> HttpResponse:
    request_headers = dict(headers)
    data: bytes | None = None

    if body is not None:
        data = json.dumps(body).encode("utf-8")
        if not any(key.lower() == "content-type" for key in request_headers):
            request_headers["Content-Type"] = "application/json"

    req = urllib_request.Request(
        url=url,
        data=data,
        headers=request_headers,
        method=method.upper(),
    )

    try:
        with urllib_request.urlopen(req, timeout=timeout) as raw_response:
            raw_body = raw_response.read()
            response_headers = {key.lower(): value for key, value in raw_response.headers.items()}
            return HttpResponse(
                status_code=raw_response.status,
                text=_decode_body(raw_body, response_headers),
                headers=response_headers,
            )
    except urllib_error.HTTPError as exc:
        # HTTP 4xx/5xx sind fuer diese Tests normale Responses und muessen
        # vom jeweiligen Evaluator bewertet werden, nicht als Clientfehler enden.
        raw_body = exc.read()
        response_headers = {key.lower(): value for key, value in exc.headers.items()}
        return HttpResponse(
            status_code=exc.code,
            text=_decode_body(raw_body, response_headers),
            headers=response_headers,
        )


def perform_request(
    reporter: Reporter,
    *,
    name: str,
    method: str,
    url: str,
    headers: Mapping[str, str],
    expectation: str,
    evaluator: Callable[[int, str, str], TestOutcome],
    body: Any = None,
    timeout: float = 10.0,
    header_name: str = "X-Admin-Key",
) -> str:
    started = time.perf_counter()
    try:
        response = _urllib_request(method, url, headers, body, timeout)
        elapsed = time.perf_counter() - started
        outcome = evaluator(response.status_code, expectation, response.text)
        return reporter.record(
            name=name,
            method=method,
            url=url,
            expectation=expectation,
            headers=headers,
            request_body=body,
            outcome=outcome,
            elapsed=elapsed,
            response=response,
            header_name=header_name,
        )
    except (socket.timeout, TimeoutError) as exc:
        elapsed = time.perf_counter() - started
        outcome = TestOutcome("FAIL", f"Timeout nach {timeout:g}s; Request wurde nicht sauber beantwortet.")
        return reporter.record(
            name=name,
            method=method,
            url=url,
            expectation=expectation,
            headers=headers,
            request_body=body,
            outcome=outcome,
            elapsed=elapsed,
            error=exc,
            header_name=header_name,
        )
    except urllib_error.URLError as exc:
        elapsed = time.perf_counter() - started
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, (socket.timeout, TimeoutError)):
            outcome = TestOutcome("FAIL", f"Timeout nach {timeout:g}s; Request wurde nicht sauber beantwortet.")
        else:
            outcome = TestOutcome("FAIL", "Server nicht erreichbar / Verbindung fehlgeschlagen.")
        return reporter.record(
            name=name,
            method=method,
            url=url,
            expectation=expectation,
            headers=headers,
            request_body=body,
            outcome=outcome,
            elapsed=elapsed,
            error=exc,
            header_name=header_name,
        )
    except Exception as exc:
        elapsed = time.perf_counter() - started
        outcome = TestOutcome("FAIL", "Unerwarteter Client-/Testfehler.")
        return reporter.record(
            name=name,
            method=method,
            url=url,
            expectation=expectation,
            headers=headers,
            request_body=body,
            outcome=outcome,
            elapsed=elapsed,
            error=exc,
            header_name=header_name,
        )
