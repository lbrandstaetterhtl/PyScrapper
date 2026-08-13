#Python Default Imports
import http.cookiejar
import urllib.request
import certifi
import ssl
import os




REQUESTS_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(REQUESTS_DIR, "cookies.txt")

class Session:
    def __init__(
        self,
        cookie_file=COOKIE_FILE
        ):

        if os.path.exists(cookie_file):
            self.cookieFile = cookie_file
        else:
            self.cookieFile = COOKIE_FILE

        self.cookieJar = http.cookiejar.MozillaCookieJar(
            self.cookieFile
        )

        self.reloadCookies()

        httpsHandler = urllib.request.HTTPSHandler(
            context=ssl.create_default_context(
                cafile=certifi.where()
            )
        )

        self.opener = urllib.request.build_opener(
            httpsHandler,
            urllib.request.HTTPCookieProcessor(
                self.cookieJar
            )
        )

        self.defaultHeaders = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/145.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,image/avif,"
                "image/webp,*/*;q=0.8"
            ),
            "Accept-Language": (
                "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"
            ),
            "Connection": "keep-alive",
            "Accept-Encoding": "identity"
        }

    def reloadCookies(self):
        try:
            self.cookieJar.clear()
        except Exception:
            pass

        if os.path.exists(self.cookieFile):
            try:
                self.cookieJar.load(
                    self.cookieFile,
                    ignore_discard=True,
                    ignore_expires=True
                )
                print(
                    f"[Session] reloaded "
                    f"{len(self.cookieJar)} cookies"
                )
            except Exception as error:
                print(
                    f"[Session] cookie reload failed: {error}"
                )
        

    def _saveCookies(self):
        self.cookieJar.save(ignore_discard=True, ignore_expires=True)

    def open(self, url: str = None ,method="GET" , request: urllib.request.Request = None, headers:dict = None, timeout:int =10):
        self._saveCookies()

        _validateArguments_sessionOpen(url, method, request, headers, timeout)

        finalHeaders = self.defaultHeaders.copy()

        if headers is not None:
            finalHeaders.update(headers)


        if url:
            _request = urllib.request.Request(
                url,
                method=method,
                headers=finalHeaders
            )
        else:
            _request = request
#Making sure every default header is set
            self._mergeHeaders(_request, finalHeaders)
        

        return self.opener.open(
            _request, 
            timeout=timeout)
    

#Takes urllib request and checks their header dictionary, if any default header is missing in urllib request, it will get added.
#If Header was given, it will get used instead of default Header
    def _mergeHeaders(self, request: urllib.request.Request, headers:dict[str, str]):
        for key, value in headers.items():

            if not any(k.lower() == key.lower() for k in request.headers):
                request.add_header(key, value)


def _validateArguments_sessionOpen(
    url: str = None ,method="GET" , request: urllib.request.Request = None, headers:dict = None, timeout=10  
):
#Core Imports
    from ..models.errors import ArgumentError
    from ..general import Validate

    if (
        (url and request)
        or (not url and not request)
    ):
        raise ArgumentError(
            argument="url, request",
            wanted_type="str, urllib.request.Request: Please provide only one and not None",
            caller="session.open",
        )
    Validate.special.validateRequestMethod(method=method, caller="[CORE] Session.open")
    Validate.general.validateInt(argument_name="timeout", integer=timeout, caller="[CORE] Session.open")
    if headers:

        Validate.general.validateDict(argument_name="headers", dictionary=headers, caller="[CORE] Session.open")
        
    if request:
        Validate.special.validateUrllibRequest(request) 
    else:
        Validate.special.validateHostDefault(url)
    
     
    