from __future__ import annotations

#Core Imports
from ...general import Validate

#Own imports
from . import helpers
from . import models

#Python default imports


#Python PIP imports
from playwright.sync_api import sync_playwright




class Browser():
    def __init__(
            self,
            url: str,
            cookie_file: str = models.COOKIE_FILE,
            log_responses: bool = True
            ):

        Validate.special.validateHostDefault(
            url=url,
            caller="[CORE] Browser.__init__"
        )

        self.cookieFilePath: str = cookie_file 
        self.startUrl: str = url
        self.running: bool = False
        self.log_responses: bool = log_responses

        self.context = None
        self.page = None
        self.browser = None
        self.playwright = None

    
        

    def _logResponse(self, response):
        request = response.request

        print(f"[CORE] Browser._handleResponse: Url -> {response.url}")
        print(f"[CORE] Browser._handleResponse: Status -> {response.status}")
        print(f"[CORE] Browser._handleResponse: Content-Type -> {response.headers.get('content-type', '')}")
        

        print(f"[CORE] Browser._handleResponse: Request Method -> {request.method}")
        print(f"[CORE] Browser._handleResponse: Request Resource Type -> {request.resource_type}")
        print(f"[CORE] Browser._handleResponse: Request Url -> {request.url}")
        print(f"[CORE] Browser._handleResponse: Request Body -> {helpers.utils.getRequestBody(response.request)}")





    def _handleResponse(self, response):
            if self.log_responses:
                self._logResponse(response)





    def run(
            self,
            headless: bool = False,
            extra_headers: dict | None = None,
            ):
        
        if not self.running:
            print(f"[CORE] Browser.run: Browser isn't running. Calling setup...")
            self.setup(
                headless,
                extra_headers
            )
        else:
            print(f"[CORE] Browser.run: Browser is already running")

        





    def setup(
            self,
            headless: bool,
            extra_headers: dict | None = None
            ):
        if self.running:
            print("[CORE] Browser.setup: Browser is already running. Aborting setup...")
            return

        
        Validate.general.validateBool(
            boolean=headless, argument_name="headless", caller="[CORE] Browser.setup"
        )
        
        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=headless,
            channel="chromium" if headless else None
        )

        self.running = True


        headers = {
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        if extra_headers:
            Validate.general.validateDict(
                argument_name="extra_headers",
                dictionary=extra_headers,
                caller="[CORE] Browser.setup"
            )
            headers.update(extra_headers)



        self.context = self.browser.new_context(
            extra_http_headers=headers,


            locale="de-DE",

            timezone_id="Europe/Vienna",

            color_scheme="dark"
        )


        cookies = helpers.cookies.loadCookies(
            self.cookieFilePath
        )

        if cookies:
            try:
                self.context.add_cookies(cookies)
                print("[CORE] Browser.setup: added Cookies to playwright context")
            except Exception as e:
                print(f"[CORE] Browser.setup: Adding cookies failed: {e}")


        self.page = self.context.new_page()

        self.page.on("response", self._handleResponse)

        self.navigate(url=self.startUrl)





    def navigate(
            self,
            url: str
            ):
        try:
            Validate.special.validateHostDefault(
                url=url,
                caller="[CORE] Browser.navigate"
            )
        except Exception as e:
            print(f"[CORE] Browser.navigate: Can't navigate to given url '{url}'. It was invalid because of the following reason: '{e}'")
        
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
            self.page.wait_for_timeout(1500)

            helpers.button.tryPressCookieAccept(
                self.page
            )

        except Exception as e:
            print(f"[CORE] Browser.navigate: Failed opening url '{url}'. Reason: {e}")





    def stop(self):
        if not self.running:
            print("[CORE] Browser.stop: Browser is already stopped")
            return


        if self.context is not None:
            helpers.cookies.saveCookies(
                self.cookieFilePath,
                browser_context=self.context
            )
            try:
                self.context.close()
            except Exception:
                pass


        if self.browser is not None:
            try:
                self.browser.close()
            except Exception:
                pass


        if self.playwright is not None:
            try:
                self.playwright.stop()
            except Exception:
                pass



        self.running = False
        self.page = None
        self.context = None
        self.browser = None

        print("[CORE] Browser.stop: Stopped browser")


    
            
    


        

        
        
            
        
