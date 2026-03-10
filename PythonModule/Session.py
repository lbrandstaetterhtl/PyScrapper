import http.cookiejar
import urllib.request
import certifi
import ssl
import os


class Session():
    def __init__(self, cookie_file="cookies.txt"):

        self.cookie_file = cookie_file

        self.cookie_jar = http.cookiejar.MozillaCookieJar(cookie_file)
        if os.path.exists(cookie_file):
            try:
                self.cookie_jar.load(ignore_discard=True, ignore_expires=True)
            except Exception:
                pass



        https_handler = urllib.request.HTTPSHandler(
            context=ssl.create_default_context(cafile=certifi.where())
        )

        self.opener = urllib.request.build_opener(
            https_handler,
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
            )
        
        self.opener.addheaders = [
            ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"),
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"),
            ("Accept-Language", "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"),
            ("Connection", "keep-alive"),
        ]

    def save_cookies(self):
        self.cookie_jar.save(ignore_discard=True, ignore_expires=True)

    def open(self, request, timeout=10):
        self.save_cookies()
        return self.opener.open(request, timeout=timeout)