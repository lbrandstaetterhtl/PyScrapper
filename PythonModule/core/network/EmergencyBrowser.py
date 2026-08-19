from __future__ import annotations
from playwright.sync_api import sync_playwright
from ..models import media
import os
import http.cookiejar
import shlex
from urllib.parse import urlparse

CONTENT_TYPE_EXTENSIONS = {
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/x-matroska": "mkv",
    "video/mp2t": "ts",

    "audio/mpeg": "mp3",
    "audio/mp4": "m4a",
    "audio/aac": "aac",
    "audio/wav": "wav",
    "audio/flac": "flac",

    "application/vnd.apple.mpegurl": "m3u8",
    "application/x-mpegurl": "m3u8",
    "application/dash+xml": "mpd",
}

REQUESTS_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(REQUESTS_DIR, "cookies.txt")

def _load_mozilla_cookies_for_playwright(cookie_file: str) -> list[dict]:
    if not os.path.exists(cookie_file):
        return []

    jar = http.cookiejar.MozillaCookieJar(cookie_file)
    try:
        jar.load(ignore_discard=True, ignore_expires=True)
    except Exception:
        return []

    cookies = []
    for c in jar:
        cookie = {
            "name": c.name,
            "value": c.value,
            "domain": c.domain,
            "path": c.path or "/",
            "secure": bool(c.secure),
            "httpOnly": False,
        }

        if c.expires is not None:
            cookie["expires"] = int(c.expires)


        cookie["sameSite"] = "Lax"

        cookies.append(cookie)

    return cookies


def _guess_File_Extension(content_type: str) -> str | None:

    content_type = content_type.split(";", 1)[0].lower()
    return CONTENT_TYPE_EXTENSIONS.get(content_type)

def _save_playwright_cookies_to_mozilla(context, cookie_file: str) -> None:
    try:
        playwright_cookies = context.cookies()
    except Exception as e:
        print(f"[Cookies] context.cookies failed: {e}")
        return

#If no Cookies from playwright, leave it as be
    if not playwright_cookies:
        print("[Cookies] no new cookies from Playwright, keeping existing cookie file")
        return

    jar = http.cookiejar.MozillaCookieJar(cookie_file)

#if cookie files exists, try loading it
    if os.path.exists(cookie_file):
        try:
            jar.load(ignore_discard=True, ignore_expires=True)
            print(f"[Cookies] loaded existing cookies: {len(jar)}")

        except Exception as e:
            print(f"[Cookies] could not load existing cookie file, keeping backup behavior: {e}")
            return
        

    added_or_updated = 0


    for c in playwright_cookies:
        domain = c.get("domain", "")
        name = c.get("name", "")
        value = c.get("value", "")

        if not domain or not name:
            continue

        expires = c.get("expires", None)

        morsel = http.cookiejar.Cookie(
            version=0,
            name=name,
            value=value,
            port=None,
            port_specified=False,
            domain=domain,
            domain_specified=bool(domain),
            domain_initial_dot=domain.startswith("."),
            path=c.get("path", "/"),
            path_specified=True,
            secure=bool(c.get("secure", False)),
            expires=int(expires) if expires else None,
            discard=False,
            comment=None,
            comment_url=None,
            rest={
                "HttpOnly": c.get("httpOnly", False),
                "SameSite": c.get("sameSite", ""),
            },
            rfc2109=False,
        )

#set_cookie only overwrites the same cookie
        jar.set_cookie(morsel)
        added_or_updated += 1

    if added_or_updated == 0:
        print("[Cookies] no valid cookies to merge, keeping existing cookie file")
        return

    tmp_file = cookie_file + ".tmp"
    backup_file = cookie_file + ".bak"

    try:
        if os.path.exists(cookie_file):
            import shutil
            shutil.copy2(cookie_file, backup_file)

        jar.save(tmp_file, ignore_discard=True, ignore_expires=True)
        os.replace(tmp_file, cookie_file)

        print(f"[Cookies] merged {added_or_updated} cookies, total now: {len(jar)}")

    except Exception as e:
        print(f"[Cookies] saving merged cookies failed: {e}")

        try:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
        except Exception:
            pass


def _tryPressCookieAccept(
    page,
    timeout_ms: int = 1200,
    wait_after_click_ms: int = 500,
) -> bool:

    selectors = [
        # Sehr häufig
        "button#onetrust-accept-btn-handler",
        "#onetrust-accept-btn-handler",

        # Sourcepoint
        "button[title='Alle akzeptieren']",
        "button[title='Accept All']",

        # Generische Buttons
        "button:has-text('Alle akzeptieren')",
        "button:has-text('Alles akzeptieren')",
        "button:has-text('Akzeptieren')",
        "button:has-text('Zustimmen')",

        "button:has-text('Accept all')",
        "button:has-text('Accept All')",
        "button:has-text('Accept')",
        "button:has-text('I agree')",
        "button:has-text('Agree')",

        # Häufige aria-label Varianten
        "button[aria-label*='accept' i]",
        "button[aria-label*='akzeptieren' i]",
        "button[aria-label*='zustimmen' i]",

        # Inputs
        "input[type='button'][value*='accept' i]",
        "input[type='submit'][value*='accept' i]",
        "input[type='button'][value*='akzeptieren' i]",
        "input[type='submit'][value*='akzeptieren' i]",
    ]

    # Cookie-Banner können auch in iframe sitzen.
    try:
        frames = list(page.frames)
    except Exception:
        frames = [page.main_frame]

    for frame in frames:

        for selector in selectors:

            try:
                locator = frame.locator(selector).first

                if locator.count() == 0:
                    continue

                if not locator.is_visible(
                    timeout=timeout_ms
                ):
                    continue

                print(
                    f"[Cookies] trying accept button: "
                    f"{selector}"
                )

                try:
                    locator.click(
                        timeout=timeout_ms
                    )

                except Exception:
                    try:
                        locator.click(
                            timeout=timeout_ms,
                            force=True
                        )
                    except Exception:
                        continue

                print(
                    "[Cookies] consent accepted"
                )

                page.wait_for_timeout(
                    wait_after_click_ms
                )

                return True

            except Exception:
                continue

    print(
        "[Cookies] no consent dialog found"
    )

    return False


def _tryPressPlay(page, max_attempts: int = 4, wait_ms: int = 2000) -> bool:
    context = page.context
    start_url = page.url

    selectors = [
        # --------------------------------------------------
        # Video.js
        # --------------------------------------------------
        ".vjs-big-play-button",
        ".video-js .vjs-big-play-button",
        "button.vjs-big-play-button",

        # --------------------------------------------------
        # JW Player
        # --------------------------------------------------
        ".jw-icon-playback",
        ".jw-display-icon-container",
        ".jwplayer .jw-display-icon-container",
        ".jwplayer .jw-icon-playback",
        ".jwplayer [aria-label*='play' i]",

        # --------------------------------------------------
        # Plyr
        # --------------------------------------------------
        ".plyr__control--overlaid",
        ".plyr__control[data-plyr='play']",
        "button[data-plyr='play']",
        ".plyr button[aria-label*='play' i]",

        # --------------------------------------------------
        # Shaka Player
        # --------------------------------------------------
        ".shaka-play-button",
        ".shaka-play-button-container button",
        ".shaka-controls-container button[aria-label*='play' i]",

        # --------------------------------------------------
        # YouTube
        # --------------------------------------------------
        ".ytp-large-play-button",
        ".ytp-play-button",
        "button.ytp-large-play-button",
        "button.ytp-play-button",

        # --------------------------------------------------
        # MediaElement.js
        # --------------------------------------------------
        ".mejs__overlay-button",
        ".mejs__play button",
        ".mejs-playpause-button button",

        # --------------------------------------------------
        # Flowplayer
        # --------------------------------------------------
        ".fp-play",
        ".fp-ui .fp-play",
        ".flowplayer .fp-play",

        # --------------------------------------------------
        # Clappr
        # --------------------------------------------------
        ".media-control-center-panel .play-wrapper",
        ".play-wrapper",
        "[data-playpause]",
        ".container[data-container] .play-wrapper",

        # --------------------------------------------------
        # Bitmovin
        # --------------------------------------------------
        ".bmpui-ui-hugeplaybacktogglebutton",
        ".bmpui-ui-playbacktogglebutton",
        "button[class*='playbacktogglebutton' i]",

        # --------------------------------------------------
        # THEOplayer
        # --------------------------------------------------
        ".theoplayer-play-button",
        ".theoplayer-control-playpause-button",
        "[class*='theoplayer'][class*='play' i]",

        # --------------------------------------------------
        # Kaltura / generic embedded players
        # --------------------------------------------------
        ".largePlayBtn",
        ".playkit-pre-playback-play-button",
        ".playkit-control-button.playkit-playback-button",

        # --------------------------------------------------
        # Odysee / LBRY / generic React players
        # --------------------------------------------------
        "button[data-testid*='play' i]",
        "[data-testid='play-button']",
        "[data-testid='playback-button']",
        "[data-testid*='playback' i]",

        # --------------------------------------------------
        # Generic IDs / classes
        # --------------------------------------------------
        "#play-button",
        "#playButton",
        "#play_button",
        "#playback-button",
        "#playback_button",

        ".play-button",
        ".playButton",
        ".play_button",
        ".playback-button",
        ".playback_button",
        ".big-play-button",
        ".bigPlayButton",

        # Your existing custom names
        "playback_button_svg",
        "playback_button",

        # --------------------------------------------------
        # Accessible buttons
        # --------------------------------------------------
        "button[aria-label='Play']",
        "button[aria-label='play']",
        "button[aria-label*='play' i]",
        "button[aria-label*='resume' i]",
        "button[aria-label*='start' i]",

        "button[aria-label*='abspielen' i]",
        "button[aria-label*='wiedergabe' i]",
        "button[aria-label*='fortsetzen' i]",
        "button[aria-label*='starten' i]",

        # --------------------------------------------------
        # Title attributes
        # --------------------------------------------------
        "button[title='Play']",
        "button[title*='play' i]",
        "button[title*='resume' i]",
        "button[title*='start' i]",

        "button[title*='abspielen' i]",
        "button[title*='wiedergabe' i]",
        "button[title*='starten' i]",

        # --------------------------------------------------
        # role=button elements
        # --------------------------------------------------
        "[role='button'][aria-label*='play' i]",
        "[role='button'][title*='play' i]",
        "[role='button'][aria-label*='abspielen' i]",
        "[role='button'][title*='abspielen' i]",

        # --------------------------------------------------
        # SVG/Icon-based buttons
        # --------------------------------------------------
        "button svg[aria-label*='play' i]",
        "button [class*='play-icon' i]",
        "button [class*='icon-play' i]",
        "[role='button'] [class*='play-icon' i]",

        # --------------------------------------------------
        # Text fallbacks
        # --------------------------------------------------
        "button:has-text('Play')",
        "button:has-text('Abspielen')",
        "button:has-text('Wiedergabe starten')",
        "button:has-text('Video starten')",

        "[role='button']:has-text('Play')",
        "[role='button']:has-text('Abspielen')",

        # --------------------------------------------------
        # Generic class/id contains play
        # Be careful: these are intentionally late
        # --------------------------------------------------
        "button[class*='play' i]",
        "button[id*='play' i]",
        "[role='button'][class*='play' i]",
        "[role='button'][id*='play' i]",

        # --------------------------------------------------
        # Last resort
        # --------------------------------------------------
        "video",
    ]

    def _is_video_playing(frame) -> bool:
        try:
            return frame.evaluate("""
                () => {
                    const mediaElements = [
                        ...document.querySelectorAll("video, audio")
                    ];

                    return mediaElements.some(media =>
                        !media.paused &&
                        !media.ended &&
                        media.readyState > 0
                    );
                }
            """)
        except Exception:
            return False

    def _looks_like_pause_button(loc) -> bool:
        try:
            aria_label = (loc.get_attribute("aria-label") or "").lower()
            title = (loc.get_attribute("title") or "").lower()
            classes = (loc.get_attribute("class") or "").lower()

            pause_keywords = (
                "pause",
                "pausieren",
            )

            return any(
                keyword in value
                for value in (aria_label, title, classes)
                for keyword in pause_keywords
            )
        except Exception:
            return False

    def _is_any_media_playing() -> bool:
        try:
            frames = list(page.frames)
        except Exception:
            frames = [page.main_frame]

        return any(
            _is_video_playing(frame)
            for frame in frames
        )

    def _try_js_play(frame) -> bool:
        try:
            return frame.evaluate("""
                async () => {
                    const v = document.querySelector("video");
                    if (!v) return false;

                    try {
                        v.muted = true;
                        const p = v.play();
                        if (p && typeof p.then === "function") {
                            await p.catch(() => {});
                        }
                    } catch (e) {}

                    return !!(
                        v.currentSrc &&
                        !v.paused &&
                        !v.ended &&
                        v.readyState >= 2
                    );
                }
            """)
        except Exception:
            return False

    def _close_new_pages(old_pages) -> bool:
        current_pages = set(context.pages)
        new_pages = current_pages - old_pages

        for p in list(new_pages):
            try:
                p.close()
            except Exception:
                pass

        return bool(new_pages)

    def _restore_page(expected_url: str):
        try:
            if page.url != expected_url:
                page.go_back(timeout=5000)
                page.wait_for_timeout(1200)
                if page.url != expected_url:
                    page.goto(expected_url, wait_until="domcontentloaded", timeout=8000)
                    page.wait_for_timeout(1500)
        except Exception:
            try:
                page.goto(expected_url, wait_until="domcontentloaded", timeout=8000)
                page.wait_for_timeout(1500)
            except Exception:
                pass

    for attempt in range(max_attempts):

        if _is_any_media_playing():
            print("[Play] Media already playing")
            return True

        print(f"[Play] Attempt {attempt + 1}/{max_attempts}")

        # WICHTIG: jedes Mal frisch holen
        expected_url = page.url or start_url
        old_pages = set(context.pages)

        try:
            frames = list(page.frames)
        except Exception:
            frames = [page.main_frame]

        clicked_anything = False

        for frame in frames:
            # Erst JS play versuchen, falls schon ein video da ist
            if _is_video_playing(frame):
                print("[Play] Video already playing")
                return True

            for selector in selectors:
                try:
                    if _is_any_media_playing():
                        print("[Play] Media already playing")
                        return True

                    loc = frame.locator(selector).first

                    if loc.count() == 0:
                        continue

                    if not loc.is_visible(timeout=700):
                        continue

                    if _looks_like_pause_button(loc):
                        print("[Play] Player already appears to be playing")
                        return True

                    print(f"[Play] Trying selector: {selector}")
                    clicked_anything = True

                    try:
                        loc.click(timeout=2000)
                    except Exception:
                        try:
                            loc.click(timeout=2000, force=True)
                        except Exception:
                            continue

                    page.wait_for_timeout(wait_ms)

                    # Popup?
                    if _close_new_pages(old_pages):
                        print("[Play] Popup/new tab detected, closed")
                        _restore_page(expected_url)
                        break  # neu scannen, nicht mit altem frame weiter

                    # Redirect?
                    if page.url != expected_url:
                        print(f"[Play] Redirect detected: {page.url}")
                        _restore_page(expected_url)
                        break  # neu scannen

                    # Läuft jetzt Video?
                    try:
                        fresh_frames = list(page.frames)
                    except Exception:
                        fresh_frames = [page.main_frame]

                    for fresh_frame in fresh_frames:
                        if _is_video_playing(fresh_frame):
                            print("[Play] Video started")
                            return True

                except Exception:
                    continue
            else:
                #for selector normal zu Ende
                continue

            #break aus selector-loop wegen redirect/popup → frame-loop auch abbrechen
            break

        # Fallback -< JS play auf frischen Frames
        try:
            fresh_frames = list(page.frames)
        except Exception:
            fresh_frames = [page.main_frame]

        for frame in fresh_frames:
            if _try_js_play(frame):
                print("[Play] Video started via JS play()")
                return True

        if not clicked_anything:
            print("[Play] No clickable play element found")
            break

    return False







    
        

def _buildCurlCommand(
    url: str,
    headers: dict[str, str],
    include_cookie_header: bool = False
) -> str:
    """
    Baut aus dem echten Playwright-Request einen kopierbaren curl-Befehl.
    Cookies werden standardmäßig NICHT inline gespeichert, weil das schnell
    private Session-Daten leakt. .
    """
    wanted_headers = [
    "user-agent",
    "accept",
    "accept-language",
    "accept-encoding",
    "range",
    "origin",
    "connection",
    "referer",
    "sec-fetch-dest",
    "sec-fetch-mode",
    "sec-fetch-site",
    "authorization",
]

    if include_cookie_header:
        wanted_headers.append("cookie")

    # playwright normale gives headers in lower case.
    normalized = {str(k).lower(): str(v) for k, v in (headers or {}).items() if v is not None}

    lines = [f"curl {shlex.quote(url)}"]

    # --compressed passt, wenn der Browser komprimierte Antworten akzeptiert.
    if normalized.get("accept-encoding"):
        lines.append("  --compressed")

    for name in wanted_headers:
        value = normalized.get(name)
        if not value:
            continue

        pretty_name = "-".join(part.capitalize() for part in name.split("-"))
        if name == "user-agent":
            pretty_name = "User-Agent"
        elif name == "accept":
            pretty_name = "Accept"
        elif name == "accept-language":
            pretty_name = "Accept-Language"
        elif name == "accept-encoding":
            pretty_name = "Accept-Encoding"
        elif name == "origin":
            pretty_name = "Origin"
        elif name == "connection":
            pretty_name = "Connection"
        elif name == "referer":
            pretty_name = "Referer"
        elif name == "authorization":
            pretty_name = "Authorization"
        elif name == "cookie":
            pretty_name = "Cookie"

        lines.append(f"  -H {shlex.quote(f'{pretty_name}: {value}')}")

    return " \\\n".join(lines)


def _buildOrigin(
    url: str
) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def _removeByteRangeParams(url: str) -> str:
    import urllib.parse

    parsed = urllib.parse.urlsplit(url)

    params_to_remove = {
        "bytestart",
        "byteend",
        "bytes",
    }

    filtered_query_parts = []

    for part in parsed.query.split("&"):
        if not part:
            continue

        key = part.split("=", 1)[0]
        key = urllib.parse.unquote_plus(key).lower()

        if key in params_to_remove:
            continue

        filtered_query_parts.append(part)

    return urllib.parse.urlunsplit((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        "&".join(filtered_query_parts),
        parsed.fragment,
    ))


def _saveMedia(
    response,
    foundMedia: dict[str, media.Media],
    cookieFile: str,
    pageUrl: str = "",
    includeCookieHeaderInCurl: bool = False
):
    request = response.request

    raw_url = response.url
    if not raw_url:
        return

    url = _removeByteRangeParams(raw_url)

    lower = url.lower()

    request_headers = request.headers or {}
    response_headers = response.headers or {}

    resource_type = request.resource_type
    content_type = response_headers.get("content-type", "")

    is_media_request = (
        resource_type == "media"

        or content_type.startswith("video/")
        or content_type.startswith("audio/")
        or "application/vnd.apple.mpegurl" in content_type
        or "application/x-mpegurl" in content_type
        or "application/dash+xml" in content_type

        or "getvid" in lower
        or ".m3u8" in lower
        or ".mpd" in lower
        or ".mp3" in lower
        or ".mkv" in lower
        or ".mp4" in lower
        or ".webm" in lower
        or ".flv" in lower
        or "videoplayback" in lower
        or ".m4a" in lower
        or "mime_type=video" in lower
        or "mime_type=audio" in lower
    )

    if not is_media_request:
        return

    print(
        "[Media] found:",
        resource_type,
        content_type,
        url
    )

    curlCommand = _buildCurlCommand(
        url,
        request_headers,
        include_cookie_header=includeCookieHeaderInCurl
    )

    _referer = request_headers.get("referer", pageUrl)
    _origin = request_headers.get(
        "origin",
        _buildOrigin(_referer) if _referer else ""
    )

    _accept = request_headers.get("accept", "")
    _authorization = request_headers.get("authorization", "")
    _userAgent = request_headers.get("user-agent", "")

    _fileExtension = _guess_File_Extension(content_type)

    _streamType, _mediaType, _priority = _guessMediaType(url, content_type)

    if url not in foundMedia:
        foundMedia[url] = media.Media(
            mediaUrl=url,
            mediaType=_mediaType,
            streamType=_streamType,
            priority=_priority,
            mediaExtension=_fileExtension,

            headers=media.Headers(
                origin=_origin,
                referer=_referer,
                accept=_accept,
                cookieFile=cookieFile,
                authorization=_authorization,
                userAgent=_userAgent
            ),

            curlCommand=curlCommand
        )
    





def _guessMediaType(
    url: str,
    content_type: str
) -> tuple[media.StreamType, media.MediaType, int]:
    import urllib.parse

    parsed = urllib.parse.urlparse(url)

    hostname = (parsed.hostname or "").lower()
    path = parsed.path.lower()
    content_type = (content_type or "").lower().split(";", 1)[0].strip()

    query = urllib.parse.parse_qs(
        parsed.query,
        keep_blank_values=True
    )

    # Only use path + query for keyword heuristics.
    # Otherwise domains like "wcostream.com" would falsely match "stream".
    searchable = f"{path}?{parsed.query.lower()}"

    badKeywords = [
        "ads",
        "banner",
        "promo",
        "tracking",
        "gambling",
        "notification",
        "bonus",
        "click",
        "redirect",
        "jwplayer6",
        "ping.gif",
    ]

    goodKeywords = [
        "stream",
        "video",
        "media",
        "playlist",
        "master",
        "index",
        "hls",
        "videoplayback",
        "cdn",
        "login",
    ]

    # --------------------------------------------------
    # YouTube / Googlevideo
    # --------------------------------------------------

    if (
        hostname.endswith("googlevideo.com")
        and path.endswith("/videoplayback")
    ):
        _streamType = media.StreamType.DIRECT
        _mediaType = media.MediaType.FILE
        _priority = 120


    # --------------------------------------------------
    # WCO-style /getvid endpoint
    # --------------------------------------------------

    elif path.rstrip("/").endswith("/getvid"):

        _streamType = media.StreamType.DIRECT
        _mediaType = media.MediaType.FILE
        _priority = 100

        if "evid" in query:
            _priority += 30

        if "json" in query:
            _priority -= 80
        else:
            _priority += 40

    # --------------------------------------------------
    # HLS by URL
    # --------------------------------------------------

    elif ".m3u8" in path:

        _streamType = media.StreamType.HLS

        filename = path.rsplit("/", 1)[-1]

        if "master" in filename:
            _mediaType = media.MediaType.MASTER_M3U8
            _priority = 110

        elif any(
            keyword in filename
            for keyword in ("index", "playlist")
        ):
            _mediaType = media.MediaType.INDEX_M3U8
            _priority = 100

        else:
            _mediaType = media.MediaType.UNKNOWN_M3U8
            _priority = 50

    # --------------------------------------------------
    # HLS by Content-Type
    # --------------------------------------------------

    elif content_type in (
        "application/vnd.apple.mpegurl",
        "application/x-mpegurl",
        "audio/mpegurl",
        "audio/x-mpegurl",
    ):
        _streamType = media.StreamType.HLS
        _mediaType = media.MediaType.UNKNOWN_M3U8
        _priority = 75

    # --------------------------------------------------
    # MPEG-DASH by URL
    # --------------------------------------------------

    elif ".mpd" in path:

        _streamType = media.StreamType.DASH
        _mediaType = media.MediaType.MASTER_MPD
        _priority = 100

    # --------------------------------------------------
    # MPEG-DASH by Content-Type
    # --------------------------------------------------

    elif content_type == "application/dash+xml":

        _streamType = media.StreamType.DASH
        _mediaType = media.MediaType.MASTER_MPD
        _priority = 90

    # --------------------------------------------------
    # Direct files by URL
    # --------------------------------------------------

    elif any(
        path.endswith(ext)
        for ext in (
            ".mp3",
            ".m4a",
            ".aac",
            ".wav",
            ".flac",
            ".mp4",
            ".mkv",
            ".webm",
            ".mov",
        )
    ):

        # DASH init fragments often look like normal MP4/WebM files
        if (
            "init" in path
            and path.endswith((".mp4", ".webm"))
        ):
            _streamType = media.StreamType.DASH
            _mediaType = media.MediaType.UNKNOWN_MPD
            _priority = 40

        else:
            _streamType = media.StreamType.DIRECT
            _mediaType = media.MediaType.FILE
            _priority = 70

    # --------------------------------------------------
    # Direct media by Content-Type
    # --------------------------------------------------

    elif (
        content_type.startswith("video/")
        or content_type.startswith("audio/")
    ):
        _streamType = media.StreamType.DIRECT
        _mediaType = media.MediaType.FILE
        _priority = 65

    # --------------------------------------------------
    # Generic binary responses
    # --------------------------------------------------

    elif content_type == "application/octet-stream":

        # Could be media, but Content-Type alone is not enough
        # to identify it safely.
        return (
            media.StreamType.UNKNOWN,
            media.MediaType.UNKNOWN,
            -1
        )

    # --------------------------------------------------
    # Unknown
    # --------------------------------------------------

    else:
        return (
            media.StreamType.UNKNOWN,
            media.MediaType.UNKNOWN,
            -1
        )

    # --------------------------------------------------
    # Generic priority adjustments
    # --------------------------------------------------

    for keyword in badKeywords:
        if keyword in searchable:
            _priority -= 20

    for keyword in goodKeywords:
        if keyword in searchable:
            _priority += 10

    return (
        _streamType,
        _mediaType,
        _priority
    )




def _buildMediaList(
    medias: dict[str, media.Media]
) -> media.MediaList | None:
    
    if not medias:
        return None


    sortedMedia = sorted(
        medias.values(),
        key=lambda media: media.priority,
        reverse=True
    )


    mediaList = media.MediaList(candidates=[])


    for item in sortedMedia[:3]:
        mediaList.add(item)


    return mediaList if mediaList.candidates else None




def _blockAds(route, request):
    url = request.url.lower()

    parsed = urlparse(url)
    host = parsed.hostname or ""
    path = parsed.path.lower()
    resource_type = request.resource_type

    bad_hosts = [
        "doubleclick.net",
        "googlesyndication.com",
        "googleadservices.com",
        "googletagmanager.com",
        "googletagservices.com",
        "google-analytics.com",
        "analytics.google.com",

        "adnxs.com",
        "adsystem.com",
        "adform.net",
        "adservice.google.com",
        "adsterra.com",
        "popads.net",
        "popcash.net",
        "propellerads.com",
        "onclickads.net",
        "exoclick.com",
        "trafficjunky.net",

        "taboola.com",
        "outbrain.com",
        "mgid.com",

        "clarity.ms",
        "hotjar.com",
        "histats.com",
    ]

    bad_path_keywords = [
        "/ads/",
        "/ad/",
        "/advert",
        "/banner",
        "/popunder",
        "/popup",
        "/clickunder",
        "/tracking",
        "/tracker",
        "/analytics",
        "/beacon",
        "/pixel",
        "/collect",
        "/stats",
        "/fbevents",
    ]

    bad_query_keywords = [
        "ad_id=",
        "adid=",
        "clickid=",
        "campaignid=",
        "advert",
        "popup",
        "popunder",
    ]

    allow_keywords = [
        ".m3u8",
        ".mpd",
        ".mp4",
        ".m4s",
        ".ts",
        ".m4a",
        ".aac",
        ".mp3",
        ".webm",
        ".vtt",
        ".srt",
        "videoplayback",
        "hls",
        "dash",
        "jw_player",
        "jwplayer",
        "player",
        "megaplay",
        "stream",
        "media",
        "video",
    ]

    suspicious_resource_words = [
        "banner",
        "advert",
        "promo",
        "popunder",
        "popup",
    ]

    # --------------------------------------------------
    # Never block obvious media/player resources
    # --------------------------------------------------

    if any(keyword in url for keyword in allow_keywords):
        return route.continue_()

    # --------------------------------------------------
    # Known ad/tracking domains
    # --------------------------------------------------

    if any(
        host == bad_host or host.endswith("." + bad_host)
        for bad_host in bad_hosts
    ):
        return route.abort()

    # --------------------------------------------------
    # Suspicious paths / query
    # --------------------------------------------------

    if any(keyword in path for keyword in bad_path_keywords):
        return route.abort()

    if any(keyword in parsed.query.lower() for keyword in bad_query_keywords):
        return route.abort()

    # --------------------------------------------------
    # Suspicious static resources
    # --------------------------------------------------

    if resource_type in (
        "image",
        "font",
        "stylesheet",
    ):
        if any(keyword in url for keyword in suspicious_resource_words):
            return route.abort()

    return route.continue_()



def BrowserDiscoverStreamURLs(
        url: str,
        headless: bool = True,
        cookie_file: str = "cookies.txt",
        ad_block: bool = False,
        extra_headers: dict[str, str] | None = None,
        include_cookie_header_in_curl: bool = False

        ) -> media.MediaList | None:
    foundMedia: dict[str, media.Media] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            channel="chromium" if headless else None
        )

        try:

    
            headers = {
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                "Upgrade-Insecure-Requests": "1",
            }

            if extra_headers:
                headers.update(extra_headers)

            context = browser.new_context(
                extra_http_headers=headers,

                viewport={
                    "width": 1920,
                    "height": 1080
                },

                locale="de-DE",

                timezone_id="Europe/Vienna",

                color_scheme="dark"
            )
            if ad_block == True:
                context.route("**/*", _blockAds)

            # alte Cookies laden
            cookies = _load_mozilla_cookies_for_playwright(cookie_file)
            if cookies:
                try:
                    context.add_cookies(cookies)
                    print("[Cookies] added to Playwright context")
                except Exception as e:
                    print(f"[Cookies] add_cookies failed: {e}")

            page = context.new_page()

            def handleResponse(response):
                _saveMedia(
                    response,
                    foundMedia,
                    cookieFile=cookie_file,
                    pageUrl=page.url if page.url else url,
                    includeCookieHeaderInCurl=include_cookie_header_in_curl
                )

            page.on("response", handleResponse)
                


#Goes to the requested website and waits a brief period of time to get ressources before trying to click something
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(1500)

                _tryPressCookieAccept(page)

                page.wait_for_selector(
                    "video, iframe, [class*='player' i], [id*='player' i]",
                    timeout=10000
                )
                
            except Exception:
                pass


            
            
#Trys to press variety of default buttons            
            _tryPressPlay(page)
            print("Now waiting for timeout")
            page.wait_for_timeout(4000)

            return _buildMediaList(foundMedia)

        finally:
            # neue Cookies zurückspeichern
            
            try:
                _save_playwright_cookies_to_mozilla(context, cookie_file)
            except Exception:
                pass
            browser.close()






def BrowserDiscoverStreamURLs_ButtonList(
        url: str,
        headless: bool = True,
        cookie_file: str = COOKIE_FILE,
        adBlock: bool = False,
        buttonList: list[str] | None = None,
        extraHeaders: dict[str, str] | None = None,
        includeCookieHeaderInCurl: bool = False
        ) -> media.MediaList | None:

    foundMedia: dict[str, media.Media] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            channel="chromium" if headless else None
        )

        try:
            headers = {
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                "Upgrade-Insecure-Requests": "1",
            }

            if extraHeaders:
                headers.update(extraHeaders)

            context = browser.new_context(
                extra_http_headers=headers,

                viewport={
                    "width": 1920,
                    "height": 1080
                },

                locale="de-DE",

                timezone_id="Europe/Vienna",

                color_scheme="dark"
            )

            if adBlock == True:
                context.route("**/*", _blockAds)

            # alte Cookies laden
            cookies = _load_mozilla_cookies_for_playwright(cookie_file)
            if cookies:
                try:
                    context.add_cookies(cookies)
                    print("[Cookies] added to Playwright context")
                except Exception as e:
                    print(f"[Cookies] add_cookies failed: {e}")

            page = context.new_page()

            def handleResponse(response):
                _saveMedia(
                    response,
                    foundMedia,
                    cookieFile=cookie_file,
                    pageUrl=page.url if page.url else url,
                    includeCookieHeaderInCurl=includeCookieHeaderInCurl
                )

            page.on("response", handleResponse)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(1500)

                _tryPressCookieAccept(page)
                page.wait_for_selector(
                    "video, iframe, [class*='player' i], [id*='player' i]",
                    timeout=10000
                )
            except Exception:
                pass

            # Buttons nacheinander drücken
            if buttonList:
                for buttonSelector in buttonList:
                    try:
                        print(f"[Button] clicking: {buttonSelector}")
                        page.locator(buttonSelector).first.click(timeout=5000)
                        page.wait_for_timeout(1000)
                    except Exception as e:
                        print(f"[Button] click failed for '{buttonSelector}': {e}")
            else:
                _tryPressPlay(page)

            page.wait_for_timeout(4000)

            

            return _buildMediaList(foundMedia)

        finally:
            # neue Cookies zurückspeichern
            try:
                _save_playwright_cookies_to_mozilla(context, cookie_file)
            except Exception:
                pass

            browser.close()





#Specialised Browser discover for wcoflix.tv because browser needs to wait at certain point!         
def WCOFLIXBrowserDiscoverStreamUrls(
        index_url: str,
        headless: bool = True,
        cookie_file: str = COOKIE_FILE,
        ad_block: bool = True,
        play_button: str = ".vjs-big-play-button",
        extra_headers: dict[str, str] | None = None,
        include_cookie_header_in_curl: bool = False
):
    
    foundMedia: dict[str, media.Media] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            channel="chromium" if headless else None
        )

        try:

    
            headers = {
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                "Upgrade-Insecure-Requests": "1",
            }

            if extra_headers:
                headers.update(extra_headers)

            context = browser.new_context(
                extra_http_headers=headers,

                viewport={
                    "width": 1920,
                    "height": 1080
                },

                locale="de-DE",

                timezone_id="Europe/Vienna",

                color_scheme="dark"
            )
            if ad_block == True:
                context.route("**/*", _blockAds)

            # alte Cookies laden
            cookies = _load_mozilla_cookies_for_playwright(cookie_file)
            if cookies:
                try:
                    context.add_cookies(cookies)
                    print("[Cookies] added to Playwright context")
                except Exception as e:
                    print(f"[Cookies] add_cookies failed: {e}")

            page = context.new_page()

#
            def handleResponse(response):
                _saveMedia(
                    response,
                    foundMedia,
                    cookieFile=cookie_file,
                    pageUrl=page.url if page.url else index_url,
                    includeCookieHeaderInCurl=include_cookie_header_in_curl
                )

            page.on("response", handleResponse)

            try:
                page.goto(index_url, wait_until="domcontentloaded", timeout=30000)

                print("[Browser] loaded index page, waiting 11 seconds...")
                page.wait_for_timeout(11_000)

                print("[Browser] clicking close button...")
                page.locator("#close-btn").click(timeout=5000)

                print("[Browser] close clicked, waiting for player navigation...")

                print("[Browser] current URL:", page.url)
                page.wait_for_timeout(1000)


                if play_button:
                    page.locator(play_button).first.click(timeout=5000)
                else:
                    page.locator(".vjs-big-play-button").first.click(timeout=5000)
                page.wait_for_timeout(4000)

#Sorts every media that was found and give back the top 3
                return _buildMediaList(foundMedia)

            except Exception as e:
                print(f"[Browser] error: {e}")
                return None


        finally:
                # Always update cookies
                
                try:
                    _save_playwright_cookies_to_mozilla(context, cookie_file)
                except Exception:
                    pass
                browser.close()


from playwright.sync_api import sync_playwright


def POTokenBrowser(
        url: str,
        headless: bool = False,
        cookie_file: str = COOKIE_FILE,
        wait: int = 4000,
        extra_headers: dict | None = None
):
    headers = {
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Upgrade-Insecure-Requests": "1",
        }
    if extra_headers:
        headers.update(extra_headers)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless
        )

        context = None

        try:
            context = browser.new_context(
                extra_http_headers=headers,

                viewport={
                    "width": 1920,
                    "height": 1080
                },

                locale="de-DE",

                timezone_id="Europe/Vienna",

                color_scheme="dark"
            )
            # Vorhandene Mozilla-/Netscape-Cookies laden
            cookies = _load_mozilla_cookies_for_playwright(
                cookie_file
            )

            if cookies:
                try:
                    context.add_cookies(cookies)
                    print(
                        f"[Cookies] {len(cookies)} cookies "
                        "added to Playwright context"
                    )
                except Exception as e:
                    print(
                        f"[Cookies] add_cookies failed: {e}"
                    )

            page = context.new_page()

            def handle_request(req):
                if "/youtubei/v1/player" in req.url:
                    print(req.post_data)

            page.on("request", handle_request)

            page.goto(url)
            page.wait_for_timeout(wait)


        finally:
            
            if context is not None:
                try:
                    _save_playwright_cookies_to_mozilla(
                        context,
                        cookie_file
                    )
                    print(
                        f"[Cookies] saved to {cookie_file}"
                    )
                except Exception as e:
                    print(
                        f"[Cookies] saving failed: {e}"
                    )

                context.close()

            browser.close()

    

def BrowserButtonPress(
        url: str,
        button_name: str | None = None,
        cookie_file: str = COOKIE_FILE,
        headless: bool = False,
        extra_headers: dict[str, str] | None = None,
        wait_before_click_ms: int = 3000,
        wait_after_click_ms: int = 3000
):
    if not isinstance(url, str):
        raise TypeError(
            f"url must be str, got {type(url).__name__}"
        )

    if not url.strip():
        raise ValueError("url must not be empty")

    if not isinstance(button_name, str):
        raise TypeError(
            f"button_name must be str, got {type(button_name).__name__}"
        )

    headers = {
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Upgrade-Insecure-Requests": "1",
    }

    if extra_headers:
        headers.update(extra_headers)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless
        )

        context = None

        try:
            context = browser.new_context(
                extra_http_headers=headers,

                viewport={
                    "width": 1920,
                    "height": 1080
                },

                locale="de-DE",

                timezone_id="Europe/Vienna",

                color_scheme="dark"
            )
            # Vorhandene Mozilla-/Netscape-Cookies laden
            cookies = _load_mozilla_cookies_for_playwright(
                cookie_file
            )

            if cookies:
                try:
                    context.add_cookies(cookies)
                    print(
                        f"[Cookies] {len(cookies)} cookies "
                        "added to Playwright context"
                    )
                except Exception as e:
                    print(
                        f"[Cookies] add_cookies failed: {e}"
                    )

            page = context.new_page()

            print(f"[Browser] opening: {url}")

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30_000
            )
            page.wait_for_timeout(1500)

            _tryPressCookieAccept(page)

            page.wait_for_timeout(wait_before_click_ms)

            print(f"[Browser] current URL: {page.url}")

            if button_name:
                button = page.locator(button_name).first

                button.wait_for(
                    state="visible",
                    timeout=5000
                )

                button.click(
                    timeout=5000
                )

                print(
                    f"[Browser] clicked button: {button_name}"
                )

                page.wait_for_timeout(wait_after_click_ms)

            return {
                "url": page.url,
                "html": page.content()
            }

        finally:
            # Neue oder aktualisierte Cookies speichern
            if context is not None:
                try:
                    _save_playwright_cookies_to_mozilla(
                        context,
                        cookie_file
                    )
                    print(
                        f"[Cookies] saved to {cookie_file}"
                    )
                except Exception as e:
                    print(
                        f"[Cookies] saving failed: {e}"
                    )

                context.close()

            browser.close()




