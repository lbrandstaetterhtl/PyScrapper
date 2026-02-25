import http.cookiejar
import urllib.request
import certifi
import ssl


class Session():
    def __init__(self):
        self.cookie_jar = http.cookiejar.CookieJar()

        https_handler = urllib.request.HTTPSHandler(
            context=ssl.create_default_context(cafile=certifi.where())
        )

        self.opener = urllib.request.build_opener(
            https_handler,
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
            )
    
    def open(self, request, timeout=10):
        return self.opener.open(request, timeout=timeout)