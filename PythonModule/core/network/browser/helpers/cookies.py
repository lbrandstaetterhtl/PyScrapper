import http.cookiejar
import os

def loadCookies(
            cookie_file: str
            ) -> list[dict]:

        if not os.path.exists(cookie_file):
            print(f"[CORE] Cookies.loadCookies: Given cookie file '{cookie_file}' doesn't exist. Can't load cookies!")
            return []

        jar = http.cookiejar.MozillaCookieJar(cookie_file)

        try:
            jar.load(ignore_discard=True, ignore_expires=True)
            print(f"[CORE] Cookies.loadCookies: loaded exesting cookie file. Jar size: {len(jar)}")

        except Exception as e:
            print(f"[CORE] Cookies.loadCookies: Cookie file was found but there was an error loading cookies: '{e}'")
            return []


        cookies:list[dict] = []

        for c in jar:
            cookie = {
            "name": c.name,
            "value": c.value,
            "domain": c.domain,
            "path": c.path or "/",
            "secure": bool(c.secure),
            "httpOnly": False,
            "sameSite" : "Lax"
        }

            if c.expires is not None:
                cookie["expires"] = int(c.expires)

            cookies.append(cookie)

        print(f"[CORE] Cookies.loadCookies: Successfully loaded {len(cookies)} cookies")
        return cookies



def saveCookies(
        cookie_file: str,
        browser_context
        ):

    try:
        playwright_cookies = browser_context.cookies()

    except Exception as e:
        print(f"[CORE] Cookies.saveCookies: Failed to get cookies from context: '{e}'")
        return

    if not playwright_cookies:
        print(f"[CORE] No new cookies from Playwright. Not chaning given cookie file '{cookie_file}'")#
        return

    jar = http.cookiejar.MozillaCookieJar(cookie_file)

    if os.path.exists(cookie_file):
        try:
            jar.load(ignore_discard=True, ignore_expires=True)
            print(f"[CORE] Cookies.saveCookies: loaded exesting cookie file. Jar size: {len(jar)}")

        except Exception as e:
            print(f"[CORE] Cookies.saveCookies: Cookie file was found but there was an error loading cookies: '{e}'")
            return []

    added_or_updated: int = 0

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

        jar.set_cookie(morsel)
        added_or_updated += 1


    if added_or_updated == 0:
        print("[Cookies] no valid cookies to merge, keeping existing cookie file")
        return

    try:
        jar.save(cookie_file, ignore_discard=True, ignore_expires=True)
        print(f"[CORE] Cookies.saveCookies: merged {added_or_updated} cookies, total now: {len(jar)}")

    except Exception as e:
        print(f"[CORE] Cookies.saveCookies: saving cookies failed: {e}")