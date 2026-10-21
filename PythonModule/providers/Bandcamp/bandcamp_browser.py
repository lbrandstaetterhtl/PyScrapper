from PythonModule.core.network import browser


class BandcampCaptchaBrowser(browser.base.Browser):
    def __init__(
            self,
            url: str,
            cookie_file: str
            ):
        super().__init__(url, cookie_file, False)


    def sendCaptchaSolutions(
            self,
            solutions: list[str]
    ) -> bool:

        oldHtml: str = self.page.content()

        for index, solution in enumerate(solutions):
            self.page.locator("#capInput").fill(solution)

            try:
                self.page.locator("#capSubmit").click(
                    no_wait_after=True,
                    timeout=5000
                )
            except Exception:
                if oldHtml != self.page.content():
                    print(f"[BROWSER] Successfully solved captcha with given solution '{solution}'. It was solution number {index}")
                    return True

        print(f"[BROWSER] Couldn't solve captcha with given solutions '{', '.join(solutions)}'")
        return False    