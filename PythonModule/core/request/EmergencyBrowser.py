from playwright.sync_api import sync_playwright
from ..models import media
import os
import http.cookiejar
import shlex
from urllib.parse import urlparse


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



def _tryPressPlay(page, max_attempts: int = 4, wait_ms: int = 2000) -> bool:
    context = page.context
    start_url = page.url

    selectors = [
        ".vjs-big-play-button",
        ".jw-icon-playback",
        ".jwplayer .jw-display-icon-container",
        ".plyr__control--overlaid",
        ".shaka-play-button",
        ".ytp-large-play-button",
        "button[aria-label*='play' i]",
        "button[title*='play' i]",
        "[aria-label*='abspielen' i]",
        "[title*='abspielen' i]",
        "video",
    ]

    def _is_video_playing(frame) -> bool:
        try:
            return frame.evaluate("""
                () => {
                    const v = document.querySelector("video");
                    if (!v) return false;
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
                    loc = frame.locator(selector).first

                    if loc.count() == 0:
                        continue
                    if not loc.is_visible(timeout=700):
                        continue

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
    includeCookieHeader: bool = False
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

    if includeCookieHeader:
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


def _saveMedia(
    request,
    foundMedia: dict[str, media.Headers],
    cookieFile: str,
    pageUrl: str = "",
    includeCookieHeaderInCurl: bool = False
):
    url: str = request.url
    if not url:
        return

    lower = url.lower()

    resource_type = getattr(request, "resource_type", "")

    is_media_request = (
        resource_type == "media"
        or "getvid" in lower
        or ".m3u8" in lower
        or ".mpd" in lower
        or ".mp3" in lower
        or ".mkv" in lower
        or ".mp4" in lower
        or ".webm" in lower
        or ".flv" in lower
        or "videoplayback" in lower
    )

    if not is_media_request:
        return

    print("[Media] found:", resource_type, url)

    headers = request.headers or {}

    curlCommand = _buildCurlCommand(
        url,
        headers,
        include_cookie_header=includeCookieHeaderInCurl
    )

    _referer = headers.get("referer", pageUrl)
    _origin = headers.get("origin", _buildOrigin(_referer) if _referer else "")
    _accept = headers.get("accept", "")
    _authorization = headers.get("authorization", "")
    _userAgent = headers.get("user-agent", "")

    _streamType, _mediaType, _priority = _guessMediaType(url)

    # getvid is often direct videostream on wco.tv
    if "getvid" in lower:
        _streamType = media.StreamType.DIRECT
        _mediaType = media.MediaType.FILE
        _priority = 95

    if url not in foundMedia:
        foundMedia[url] = media.Media(
            mediaUrl=url,
            mediaType=_mediaType,
            streamType=_streamType,
            priority=_priority,
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
    url: str
) -> tuple[media.StreamType, media.MediaType, int]:
    
    lower = url.lower()


    badKeywords = [
        "ads", "banner", "promo", "tracking",
        "gambling", "notification", "bonus",
        "click", "redirect"
    ]

    goodKeywords = [
        "stream", "video", "media", "playlist",
        "master", "index", "hls", "videoplayback"
    ]


#Youtube/google videos often don't have file endings
#Youtube sadly doesn't work tho
    if "googlevideo.com" in lower and "videoplayback" in lower:
        _streamType = media.StreamType.DIRECT
        _mediaType = media.MediaType.FILE
        _priority = 100

    elif ".m3u8" in lower:
        _streamType = media.StreamType.HLS

        if "master" in lower:
            _priority = 100
            _mediaType = media.MediaType.MASTER_M3U8
        elif "index" in lower:
            _priority = 90
            _mediaType = media.MediaType.INDEX_M3U8
        else:
            _priority = 70
            _mediaType = media.MediaType.UNKNOWN_M3U8

    elif ".mpd" in lower:
        _priority = 80
        _mediaType = media.MediaType.MASTER_MPD
        _streamType = media.StreamType.DASH

    elif any(ext in lower for ext in (".mp3", ".mkv", ".mp4", ".webm")):
        if "init" in lower and (
            ".mp4" in lower or ".webm" in lower
        ):
            _priority = 40
            _mediaType = media.MediaType.UNKNOWN_MPD
            _streamType = media.StreamType.DASH
        else:
            _priority = 50
            _mediaType = media.MediaType.FILE
            _streamType = media.StreamType.DIRECT

    else:
        return (
            media.StreamType.UNKNOWN,
            media.MediaType.UNKNOWN,
            -1
        )

    if any(k in lower for k in badKeywords):
        _priority -= 50

    if any(k in lower for k in goodKeywords):
        _priority += 30

    return _streamType, _mediaType, _priority




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

    host = parsed.netloc.lower()

    path = parsed.path.lower()

    resource_type = request.resource_type

#Very very bad hosts!
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

        "facebook.net",
        "facebook.com/tr",
        "clarity.ms",
        "hotjar.com",
        "histats.com",
        "yandex.ru/metrika",
        "yandex.net",
    ]

    # Typische Ad-/Tracker-Pfade
    bad_path_keywords = [
        "/ads/",
        "/ad/",
        "/advert",
        "/banner",
        "/popunder",
        "/popup",
        "/clickunder",
        "/tracking",
        "/track",
        "/analytics",
        "/beacon",
        "/pixel",
        "/collect",
        "/stats",
        "/tag.js",
        "/gtag/js",
        "/fbevents",
    ]

    # Sehr verdächtige Query-Parameter
    bad_query_keywords = [
        "utm_source=",
        "utm_campaign=",
        "ad_id=",
        "adid=",
        "clickid=",
        "campaignid=",
        "tracking",
        "advert",
        "popup",
        "popunder",
    ]

    # Never block -> Player/Video relevant ressources
    allow_keywords = [
        ".m3u8",
        ".mpd",
        ".mp4",
        ".m4s",
        ".ts",
        ".vtt",
        ".srt",
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

    suspicious_image_words = [
                "banner",
                "advert",
                "ads",
                "promo",
            ]


    if any(good in url for good in allow_keywords):
        return route.continue_()


    if any(bad in host for bad in bad_hosts):
        return route.abort()


    if any(bad in path for bad in bad_path_keywords):
        return route.abort()


    if any(bad in url for bad in bad_query_keywords):
        return route.abort()

#Optional -> if xy ressource types have bad key words then it will will be blocked
    if resource_type in ("image", "media", "font"):
        
        if any(k in url for k in suspicious_image_words):
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
        browserLauncher = getattr(p, "chromium")
        browser = browserLauncher.launch(headless=headless)

        try:

    
            headers = {
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                "Upgrade-Insecure-Requests": "1",
            }

            if extra_headers:
                headers.update(extra_headers)

            context = browser.new_context(extra_http_headers=headers)
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
                    cookieFile = cookie_file,
                    pageUrl=page.url if page.url else url,
                    includeCookieHeaderInCurl=include_cookie_header_in_curl

                )
                

            page.on("request", handleResponse)

#Goes to the requested website and waits a brief period of time to get ressources before trying to click something
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(4000)
            except Exception:
                pass


            
            
#Trys to press variety of default buttons            
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
        browserLauncher = getattr(p, "chromium")
        browser = browserLauncher.launch(headless=headless)

        try:
            headers = {
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                "Upgrade-Insecure-Requests": "1",
            }

            if extraHeaders:
                headers.update(extraHeaders)

            context = browser.new_context(extra_http_headers=headers)

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

            def handleResponse(request):
                _saveMedia(
                    request,
                    foundMedia,
                    cookieFile=cookie_file,
                    pageUrl=page.url if page.url else url,
                    includeCookieHeaderInCurl=includeCookieHeaderInCurl
                )

            page.on("request", handleResponse)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(4000)
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
        browserLauncher = getattr(p, "chromium")
        browser = browserLauncher.launch(headless=headless)

        try:

    
            headers = {
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                "Upgrade-Insecure-Requests": "1",
            }

            if extra_headers:
                headers.update(extra_headers)

            context = browser.new_context(extra_http_headers=headers)
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
                    cookieFile = cookie_file,
                    pageUrl=page.url if page.url else index_url,
                    includeCookieHeaderInCurl=include_cookie_header_in_curl

                )
                
#If target website sends any kind of response, handleResponse function will get called
            page.on("request", handleResponse)


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
                extra_http_headers=headers
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