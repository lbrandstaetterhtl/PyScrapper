from PythonModule.core.network import browser


class BandcampCaptchaBrowser(browser.base.Browser):
    def __init__(
            self,
            url: str,
            cookie_file: str
            ):
        super().__init__(url, cookie_file, False)


    def sendCaptchaSolution(#
            self,
            solutions: list[str]
    ) -> bool:

        oldHtml: str = self.page.content()

        for solution in solutions:
            self.page.locator("#capInput").fill(solution)

            self.page.locator("#capSubmit").click()

            if oldHtml != self.page.content():
                print(f"[BROWSER] Successfully solved captcha with given solution '{solution}'")
                return True

        print(f"[BROWSER] Couldn't solve captcha with given solutions '{', '.join(solutions)}'")
        return False    