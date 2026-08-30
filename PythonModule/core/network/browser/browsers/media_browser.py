#Core imports
from ....general import Validate
from ....models import media

#Own imports
from ..base import Browser
from .. import models
from .. import helpers

class MediaBrowser(Browser):
    def __init__(
            self,
            url,
            cookie_file = models.COOKIE_FILE,
            play_button_selectors: list[str] = models.PLAY_BUTTON_SELECTORS
            ):

        Validate.general.validateListStr(
            argument_name="play_button_selectors", liste=play_button_selectors, caller="[CORE] MediaBrowser.__init__"
        )
        self.playbuttonSelectors = play_button_selectors

        self.mediaList: list[media.Media2] = []
        self.unknownList: list = []

        super().__init__(url, cookie_file, False)



    def run(
        self,
        headless: bool = False,
        extra_headers: dict | None = None,
        wait_ms: int = 4000

        ):
        Validate.general.validateInt(
            argument_name="wait_ms",
            integer=wait_ms,
            caller="[CORE] MediaBrowser.run"
        )
        super().run(headless, extra_headers)
        try:
            self.page.wait_for_selector(
                """
                video,
                audio,
                iframe,
                div[class*='player' i],
                div[id*='player' i]
                """,
                timeout=10000
            )
        except Exception:
            pass

        helpers.button.tryPressPlay(
            self.page,
            own_selectors=self.playbuttonSelectors
        )

        self.page.wait_for_timeout(wait_ms)


    def _handleResponse(
            self,
            response
            ):
        if not response.url:
            return
        
        url = response.url.lower()
        
        responseHeaders: dict = response.headers or {}
        contentType: str = responseHeaders.get("content-type", "")


        request = response.request
        ressourceType: str = request.resource_type
        requestHeaders: dict = request.headers or {}
        body = None
        try:
            body = response.body()
        except Exception:
            pass
        foundMedia = media.Media2(
                    response_url=helpers.utils.removeByteRangeParams(response.url),
                    response_status=response.status,
                    response_headers=responseHeaders,
                    request_url=request.url,
                    request_body=helpers.utils.getRequestBody(request),
                    request_headers=requestHeaders,
                    response_body=body
                )

        if not (
            ressourceType == "media"
    
            or contentType.startswith("video/")
            or contentType.startswith("audio/")
            or "application/vnd.apple.mpegurl" in contentType
            or "application/x-mpegurl" in contentType
            or "application/dash+xml" in contentType
    
            or "getvid" in url
            or ".m3u8" in url
            or ".mpd" in url
            or ".mp3" in url
            or ".mkv" in url
            or ".mp4" in url
            or ".webm" in url
            or ".flv" in url
            or "videoplayback" in url
            or ".m4a" in url
            or "mime_type=video" in url
            or "mime_type=audio" in url
        ):
            
            print(f"[CORE] MediaBrowser._handleResponse: Found unknown media.\nUrl: {url}\nContent-Type: {contentType}")
            self.unknownList.append(foundMedia)
        
        else:
            print(f"[CORE] MediaBrowser._handleResponse: Found valid media.\nUrl: {url}\nContent-Type: {contentType}")
            self.mediaList.append(foundMedia)


    def stop(self) -> tuple[list[media.Media2], list]:
        super().stop()
        return (self.mediaList, self.unknownList)


        

        