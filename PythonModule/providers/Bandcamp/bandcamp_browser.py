from PythonModule.core.network import browser


class BandcampCaptchaBrowser(browser.base.Browser):
    def __init__(
            self,
            url: str,
            cookie_file: str
            ):
        super().__init__(url, cookie_file, False)


    def sendCaptchaSolution(
            solution: str
    ):
        pass