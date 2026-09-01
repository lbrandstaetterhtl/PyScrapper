import PythonModule.core as core
from PythonModule.core.network import browser
from PythonModule.core.network.browser.models import COOKIE_FILE, PLAY_BUTTON_SELECTORS

from .. import models

#Python default imports
import os

ROOT_DIR = os.getcwd()
COOKIE_FILE = os.path.join(ROOT_DIR, "cookies.txt")

class SoundcloudMediaBrowser(browser.MediaBrowser):
    def __init__(
            self, 
            url, 
            cookie_file=COOKIE_FILE,
            ):
        
        core.general.Validate.special.validateHostPro(
            url=url,
            allowed_hostnames_list=[
                "soundcloud.com",
                "www.soundcloud.com"
            ],
            caller="[Soundcloud] SoundcloudMediaBrowser.__init__"
        )
        
        super().__init__(
            url,
            cookie_file,
            play_button_selectors=[
                ".soundTitle__playButtonHero a.sc-button-play",
                ".soundTitle__playButton a.sc-button-play"
                
            ]
            )


    def _handleResponse(
            self,
            response
    ):
        if not response.url:
            return

        urlLower = response.url.lower()
        headers = response.headers or {}

        if any(keyword in urlLower for keyword in [
            "ctr-encrypted-hls",
            "cbc-encrypted-hls",
            "widevine",
        ]):
            
            self.fatalError = core.models.errors.DRMProtectedMediaError(
                detected_url=response.url,
                source_url=self.startUrl,
                caller="[Soundcloud] SoundcloudMediaBrowser._handleResponse",
                drm_type="Widevine"
            )
            return

        if not browser.helpers.utils.isMediaResponse(
            urlLower,
            headers.get('Content-type', ""),
            response.request.resource_type
        ):
            return


        

        media = None
        if "playback.media-streaming.soundcloud.cloud" in urlLower:
            
            if "m3u8" in urlLower:
                prio = 50
                if "master" in urlLower:
                    prio = 300
                elif any(keyword in urlLower for keyword in ["index", "playlist"]):
                    prio = 250

                if "/aac_160k/" in urlLower:
                    prio += 50

                elif "/aac_96k/" in urlLower:
                    prio += 20

                media = models.FoundMedia(
                    url=response.url,
                    prio=prio,
                    stream_type=core.models.Download.DownloadType.HLS,
                    extension="m4a",
                    mime_type="audio/mp4",
                    media_type="audio",
                    extra_headers=response.headers or {}
                )


        elif "cf-hls-media.sndcdn.com/" in urlLower:
            if "m3u8" in urlLower:
                prio = 50
                if "master" in urlLower:
                    prio = 200
                elif any(keyword in urlLower for keyword in ["index", "playlist"]):
                    prio = 175

                media = models.FoundMedia(
                    url=response.url,
                    extension="mp3",
                    prio=prio,
                    stream_type=core.models.Download.DownloadType.HLS,
                    mime_type="audio/mpeg",
                    media_type="audio",
                    extra_headers=response.headers or {}
                )


        elif "cf-hls-opus-media.sndcdn.com/" in urlLower:
            if "m3u8" in urlLower:
                prio = 50
                if "master" in urlLower:
                    prio = 225
                elif any(keyword in urlLower for keyword in ["index", "playlist"]):
                    prio = 210

                media = models.FoundMedia(
                    url=response.url,
                    extension="opus",
                    prio=prio,
                    stream_type=core.models.Download.DownloadType.HLS,
                    mime_type="audio/ogg",
                    media_type="audio",
                    extra_headers=response.headers or {}
                )

        elif "cf-media.sndcdn.com/" in urlLower:
            if ".mp3" in urlLower:
                media = models.FoundMedia(
                    url=response.url,
                    extension="mp3",
                    prio=150,
                    stream_type=core.models.Download.DownloadType.FILE,
                    mime_type="audio/mpeg",
                    media_type="audio",
                    extra_headers=response.headers or {}
                )


        if media:
            self.mediaList.append(media)



            

            