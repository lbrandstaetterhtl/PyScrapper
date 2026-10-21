#Core imports
import PythonModule.core as core

from PythonModule.core.network import Session
from PythonModule.models.requests import SearchFilters

from PythonModule.core.network import html

CAPTCHA_RETRYS: int = 3

#Own imports
import captcha_ocr
from .bandcamp_browser import BandcampCaptchaBrowser

#Python default imports
import urllib.parse
import base64
from datetime import datetime
import os

OCR_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "ocr", "model.safetensors")
)

class CaptchaDetected(Exception):...



def search(
        search_term: str,
        filters: SearchFilters,
        session: Session,
        top: int = 5
) -> list[dict]:
    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term,
                                              caller="[providers] Bandcamp.search")
    core.general.Validate.general.validateGeneralType(argument_name="filters", obj=filters, objType=SearchFilters,
                                                      caller="[providers] Bandcamp.search")
    core.general.Validate.special.validateSession(session=session, argument_name="session",
                                                  caller="[providers] Bandcamp.search")
    core.general.Validate.general.validateInt(argument_name="top", integer=top, caller="[providers] Bandcamp.search")

    searchURL = _buildSearchUrl(search_term=search_term)

    def _getSearchHtml():
        searchHtml = html.getHtml(
            url=searchURL,
            session=session
        )
        if not searchHtml:
            raise core.models.errors.TaskFailedError(
                task="_getsearchHtml",
                reason=f"Couldn't retrieve non-empty HTML - '{searchURL}'",
                caller="[providers] Bandcamp.search"
            ) 
        return searchHtml
    
    retrys = 0

    while True:
        try:
        
            searchHtml: str = _getSearchHtml()

            if _isClientChallenge(searchHtml):
                raise CaptchaDetected

            results: list[dict] = []

            trackPattern: str = r'<li class="searchresult.*?</li>'
            allTracks: list[str] = core.general.DataSearch.searchBlocksAll(
                pattern=trackPattern,
                search_block=searchHtml,
                return_regex_exception=False
            )

            if not allTracks:
                raise core.models.errors.TaskFailedError(
                    task="get allTracks",
                    reason="Couldn't find capture group with given pattern",
                    caller="[providers] Bandcamp.search",
                    extraMessages=[
                        f"Used Pattern: '{trackPattern}'",
                        f"Searched variable: 'searchHtml'"
                    ]
                )

            type_pattern = r'data-search=.*?(?:&quot;|")type(?:&quot;|")\s*:\s*(?:&quot;|")(.*?)(?:&quot;|")'

            for track in allTracks:

                if len(results) >= top:
                    break

                trackType = core.general.DataSearch.searchBlocks(
                    pattern=type_pattern,
                    search_block=track,
                    return_regex_exception=False
                )
                if not trackType:
                    continue
         

                MyType = _typeMapping(trackType)
    

                # Default "nothing" that gets sent for tags is [''] that's why filtering for that
                if filters.tags != ['']:
                    if MyType not in filters.tags:
                        continue

                
                result = _buildResult(track)
                if result:
                    result["type"] = MyType
                    results.append(result)

            return results



        except CaptchaDetected:
            retrys += 1
            if retrys >= CAPTCHA_RETRYS:
                raise core.models.errors.TaskFailedError(
                    task="Bandcamp.search.solveCaptcha",
                    reason=f"CAPTCHA challenge persisted after {CAPTCHA_RETRYS} solving attempts",
                    caller="[providers] Bandcamp.search",
                    extraMessages=[
                        "OCR Captcha Handler couldn't solve required captcha for search",
                        "Please contact an admin to do it manually or try again"
                    ]
                )

            _solveCaptcha(searchURL, session.cookieFile)
            session.reloadCookies()

            
            

    

def _solveCaptcha(url: str, cookie_file: str) -> None:
    captchaBrowser = BandcampCaptchaBrowser(
        url=url,
        cookie_file=cookie_file
    )
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    
    tmpFile = f"{now}-Bandcamp-captcha.jpeg"

    try:
        captchaBrowser.run(headless=True)

        browserHtml = captchaBrowser.page.content()

        image_data_pattern: str = r'<img.*?src="data:image/jpeg;base64,(.*?)"'
        image_data_base64 = core.general.DataSearch.searchBlocks(
            pattern=image_data_pattern,
            search_block=browserHtml,
            return_regex_exception=False
        )
        if not image_data_base64:
            raise core.models.errors.TaskFailedError(
                task="Bandcamp.solveCaptcha.extractImage",
                reason="Couldn't find CAPTCHA image in browser HTML",
                caller="[providers] Bandcamp._solveCaptcha",
                extraMessages=[
                    f"URL: {url}",
                    f"Pattern: {image_data_pattern}"
                ]
            )

        

        with open(tmpFile, "wb") as file:
            file.write(base64.b64decode(image_data_base64, validate=True))

        absolutePath: str = os.path.abspath(tmpFile)

        solutions: list[str] = captcha_ocr.img_to_text(absolutePath, OCR_PATH, 5)

        captchaBrowser.sendCaptchaSolutions(solutions)

    except Exception as e:
        raise core.models.errors.TaskFailedError(
            task="Bandcamp.solveCaptcha.OCR",
            reason="OCR inference failed",
            caller="[providers] Bandcamp._solveCaptcha",
            extraMessages=[
                f"Model path: {OCR_PATH}",
                f"Original exception: {type(e).__name__}: {e}"
            ]
        ) from e
    

    finally:
        if os.path.exists(tmpFile):
            os.remove(tmpFile)

        captchaBrowser.stop()

        
    
    

CLIENT_CHALLENGE_MARKERS = (
    "<title>Client Challenge</title>",
    "/_fs-ch-"
)





def _isClientChallenge(
        page_html: str
) -> bool:
    if not isinstance(page_html, str):
        return False

    return any(marker in page_html for marker in CLIENT_CHALLENGE_MARKERS)





def _buildSearchUrl(
        search_term: str,

) -> list[str]:
    base_url = "https://bandcamp.com/search?"

    params = {
        "q": search_term
    }
    searchURL = base_url + urllib.parse.urlencode(params)
    return searchURL








def _buildResult(
        track: str,
) -> dict | None:
    
    dictionary = {}
    try:
        thumbnail_pattern = r'<img src="(.*?)">'

        dictionary['thumbnail'] = core.general.DataSearch.searchBlocks(
            pattern=thumbnail_pattern,
            search_block=track,
            return_regex_exception=True
        )
        titel_pattern = r'<div class="heading">.*?<a.*?>(.*?)</a>'
        dictionary['title'] = core.general.DataSearch.searchBlocks(
            pattern=titel_pattern,
            search_block=track,
            return_regex_exception=True
        )

        url_pattern = r'<div class="heading">.*?<a href="(.*?)"'
        dictionary['url'] = core.general.DataSearch.searchBlocks(
            pattern=url_pattern,
            search_block=track,
            return_regex_exception=True
        )
    except core.models.errors.RegexSearchError:
        return None

    return dictionary





def _typeMapping(givenType: str) -> str:
    mapping = {
        "t": "track",
        "a": "album",
        "b": "creator"
    }
    return mapping.get(givenType, None)