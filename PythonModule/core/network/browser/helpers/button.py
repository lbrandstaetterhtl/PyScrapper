#Own imports
from .. import models






def tryPressPlay(
        page, max_attempts: int = 4,
        wait_ms: int = 2000,
        own_selectors: list[str] | None = None

        ) -> bool:
    context = page.context
    start_url = page.url


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

            for selector in models.PLAY_BUTTON_SELECTORS if own_selectors is None else own_selectors:
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

        # Fallback -> JS play auf frischen Frames
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






def tryPressSkip(
    page,
    timeout_ms=4000,
    own_selectors: list[str] | None = None
):
    try:
        frames = list(page.frames)
    except Exception:
        frames = [page.main_frame]

    for frame in frames:
        for button_name in models.AD_SKIP_BUTTON_NAMES if own_selectors is None else own_selectors:
            try:
                locator = frame.get_by_role(
                    "button",
                    name=button_name,
                    exact=True
                ).first

                if locator.count() == 0:
                    continue

                try:
                    locator.wait_for(
                        state="visible",
                        timeout=timeout_ms
                    )
                except Exception:
                    continue

                print(
                    f"[BROWSER] Trying AD skip button: "
                    f"{button_name}"
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
                    f"[BROWSER] AD skip button pressed: "
                    f"{button_name}"
                )

                return True

            except Exception:
                continue

    return False






def tryPressCookieAccept(
    page,
    timeout_ms: int = 1200,
    wait_after_click_ms: int = 500,
    own_selectors: list[str] | None = None
) -> bool:

    

    # Cookie-Banner können auch in iframe sitzen.
    try:
        frames = list(page.frames)
    except Exception:
        frames = [page.main_frame]

    for frame in frames:

        for selector in models.COOKIE_ACCEPT_SELECTORS if own_selectors is None else own_selectors:

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