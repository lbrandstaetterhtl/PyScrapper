import PythonModule.core as core
from PythonModule.core.network import browser
from PythonModule.core.network.browser.models import COOKIE_FILE, PLAY_BUTTON_SELECTORS

from .. import models

#Python default imports
import os
import urllib.parse
import time


ITAG_PRIORITY = {
    # Video + Audio
    "22": 100,   # MP4 720p + audio
    "18": 90,    # MP4 360p + audio
    "17": 80,    # 3GP low quality

    # Audio only
    "251": 70,   # WebM Opus ~160 kbps
    "141": 68,   # M4A AAC ~256 kbps (wenn verfügbar)
    "140": 65,   # M4A AAC ~128 kbps
    "250": 60,   # WebM Opus ~70 kbps
    "249": 55,   # WebM Opus ~50 kbps
    "139": 50,   # M4A AAC low quality

    # Video only
    "313": 30,
    "271": 29,
    "248": 28,
    "247": 27,
    "244": 26,
    "243": 25,
    "242": 24,
    "278": 23,

    "137": 22,
    "136": 21,
    "135": 20,
    "134": 19,
    "133": 18,
    "160": 17,
}

ITAG_RESOLVE_TYPE = {
    # Video + Audio
    "22": "video",
    "18": "video",
    "17": "video",

    # Audio only
    "251": "audio",
    "141": "audio",
    "140": "audio",
    "250": "audio",
    "249": "audio",
    "139": "audio",

    # Video only
    "313": "video-only",
    "271": "video-only",
    "248": "video-only",
    "247": "video-only",
    "244": "video-only",
    "243": "video-only",
    "242": "video-only",
    "278": "video-only",

    "137": "video-only",
    "136": "video-only",
    "135": "video-only",
    "134": "video-only",
    "133": "video-only",
    "160": "video-only",
}

class YoutubeMusicMediaBrowser(browser.MediaBrowser):
    def __init__(
            self, 
            url, 
            cookie_file=COOKIE_FILE,
            ):
        
        core.general.Validate.special.validateHostPro(
            url=url,
            allowed_hostnames_list=[
                "music.youtube.com",
                "www.music.youtube.com"
            ],
            caller="[Youtube] YoutubeMusicMediaBrowser.__init__"
        )
        
        super().__init__(
            url,
            cookie_file,
            play_button_selectors=[
                ".ytmusic-player-bar .play-pause-button"
                
            ]
            )

        


    def _handleResponse(
            self,
            response
    ):

        if _youtubeAdShowing(self.page):
            print("[Youtube] Ad detected, skipping response handling")
            return
    
        if not response.url:
            return

        urlLower = response.url.lower()
        headers = response.headers or {}
        parsedUrl = urllib.parse.urlparse(response.url)
        query = urllib.parse.parse_qs(parsedUrl.query)

        

        if not browser.helpers.utils.isMediaResponse(
            urlLower,
            headers.get('content-type', ""),
            response.request.resource_type
        ):
            return

        if not ".googlevideo.com/videoplayback" in urlLower or not "range=" in urlLower:
            return

        itag = query.get("itag", [None])[0]
        totalSize = query.get("clen",[None])[0]

        if not itag or not totalSize:
            return


        prio = ITAG_PRIORITY.get(itag, -1)
        if prio < 0:
            return

        mediaType = ITAG_RESOLVE_TYPE.get(itag, "unknown")

        if mediaType == "unknown":
            return

        

        curRange = query.get("range", [None])[0]
        if not curRange:
            return

        try:
            rangeStart = int(
                curRange.split("-", 1)[0]
            )
        except (ValueError, IndexError):
            rangeStart = None

        if rangeStart is not None and rangeStart != 0:
            print(
                f"[Youtube] UMP candidate starts at "
                f"{rangeStart}, forcing initial range"
            )

            query["range"] = ["0-65000"]

            resolvedUrl = urllib.parse.urlunparse(
            parsedUrl._replace(
                query=urllib.parse.urlencode(
                    query,
                    doseq=True
                )
            )
        )
        else:
            resolvedUrl = response.url
        

        media = models.FoundMedia(
            url=resolvedUrl,
            prio=prio,
            media_type=mediaType,
            extra_headers=response.request.all_headers() or {},
            mime_type=headers.get('content-type', ""),
            total_size=int(totalSize),
            extension = "webm",
            stream_type=core.models.Download.DownloadType.UMP,
            post_body = response.request.post_data_buffer or None
        )

        self.mediaList.append(media)





        
class YoutubeMusicTokenBrowser(browser.MediaBrowser):
    def __init__(
            self, 
            url, 
            cookie_file=COOKIE_FILE,
            ):
        
        core.general.Validate.special.validateHostPro(
            url=url,
            allowed_hostnames_list=[
                "music.youtube.com",
                "www.music.youtube.com"
            ],
            caller="[Youtube] YoutubeMusicTokenBrowser.__init__"
        )
        self.token : str | None = None 
        super().__init__(
            url,
            cookie_file,
            play_button_selectors=[
                ".ytmusic-player-bar .play-pause-button"     
            ]
            )

        
    def run(
            self,
            headless: bool = False,
            extra_headers: dict | None = None,
            timeout_ms: int = 4000,
    
            ):
            core.general.Validate.general.validateInt(
                argument_name="timeout_ms",
                integer=timeout_ms,
                caller="[CORE] MediaBrowser.run"
            )
            super().run(headless, extra_headers, 1)
    
            deadline = time.monotonic() + timeout_ms / 1000
    
            browser.helpers.button.tryPressPlay(
                self.page,
                own_selectors=self.playbuttonSelectors
            )

            while self.token is None:
                self._raiseFatalError()

                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        "YouTube Music did not produce a valid "
                        "per-video PO token within "
                        f"{timeout_ms} ms"
                    )

                self.page.wait_for_timeout(200)



    

        


    def _handleResponse(
            self,
            response
    ):

        if not response.url:
            return

        if _youtubeAdShowing(self.page):
            print("[Youtube] Ad detected, skipping response handling")
            return

    
        parsedUrl = urllib.parse.urlparse(response.url)
        

        

        if not browser.helpers.utils.isMediaResponse(
            response.url.lower(),
            response.headers.get('content-type', ""),
            response.request.resource_type
        ):
            return

        if not ".googlevideo.com/videoplayback" in response.url:
            return

        if not "ump=1" in response.url.lower():
            return

        contentType = (
            response.headers
            or {}
        ).get("content-type", "").lower()

        if "application/vnd.yt-ump" not in contentType:
            return

        query = urllib.parse.parse_qs(
            parsedUrl.query,
            keep_blank_values=True,
        )

        token = query.get("pot", [None])[0]

        if not token:
            print("[Youtube] UMP candidate has no PO token")
            return

        try:
            responseBody = response.body()
            protectionStatus = (
                core.download.UMP.download.getStreamProtectionStatus(responseBody)
            )
        except Exception as e:
            print(
                "[Youtube] Could not inspect UMP protection "
                f"status: {e}"
            )
            return

        print(
            "[Youtube] UMP protection status:",
            protectionStatus,
        )

        if protectionStatus == 2:
            print(
                "[Youtube] Cold-start token detected; "
                "waiting for final token"
            )
            return

        if protectionStatus == 3:
            print(
                "[Youtube] Attestation required; "
                "waiting for another request"
            )
            return

        if protectionStatus != 1:
            return

        print("[Youtube] Valid per-video PO token found")

        self.token = token
        self.tokenUrl = response.url
        self.tokenHeaders = response.request.all_headers()

    def stop(self):
        super().stop()
        return self.token





        
def _youtubeAdShowing(page) -> bool:
    try:
        return page.locator(
            "#movie_player.ad-showing, "
            "#movie_player.ad-interrupting"
        ).count() > 0
    except Exception:
        return False
        

