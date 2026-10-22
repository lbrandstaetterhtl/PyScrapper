#Core imports
import PythonModule.core as core

from PythonModule.core.network import Session
from PythonModule.models.requests import SearchFilters

from PythonModule.core.network import html



#Own imports
import captcha_ocr
from .bandcamp_browser import BandcampCaptchaBrowser

#Python default imports
import urllib.parse
import base64
from datetime import datetime
import os
import json

OCR_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "ocr", "model.safetensors")
)


CAPTCHA_RETRIES: int = 3



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

    searchURL = _buildSearchUrl(
        search_term=search_term,
        search_filters=filters
        )

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

    usedUrls = set()
    results: list[dict] = []

    def _addResult(result: dict):

        if not result:
            return

        if result["url"] in usedUrls:
            return
        
        results.append(result)
        usedUrls.add(result["url"])


    while True:
        try:
        
            searchHtml: str = _getSearchHtml()

            if _isClientChallenge(searchHtml):
                raise CaptchaDetected

            

            trackPattern: str = r'<li class="searchresult.*?</li>'
            resources: list[str] = core.general.DataSearch.searchBlocksAll(
                pattern=trackPattern,
                search_block=searchHtml,
                return_regex_exception=False
            )

            if not resources:
                raise core.models.errors.TaskFailedError(
                    task="get resources",
                    reason="Couldn't find capture group with given pattern",
                    caller="[providers] Bandcamp.search",
                    extraMessages=[
                        f"Used Pattern: '{trackPattern}'",
                        f"Searched variable: 'searchHtml'"
                    ]
                )

            type_pattern = r'data-search=.*?(?:&quot;|")type(?:&quot;|")\s*:\s*(?:&quot;|")(.*?)(?:&quot;|")'

            for resource in resources:

                if len(results) >= top:
                    break

                trackType = core.general.DataSearch.searchBlocks(
                    pattern=type_pattern,
                    search_block=resource,
                    return_regex_exception=False
                )
                if not trackType:
                    continue

                resourceType = _typeMapping(trackType)

                # Default "nothing" that gets sent for tags is [''] that's why filtering for that
                if filters.tags not in ([], ['']):
                    if resourceType not in filters.tags:
                        continue
            

                if resourceType == "track":
                    result = _buildResult(resource)

                    _addResult(result)

                elif resourceType == "album":
                
                    for result in _getTrackResultsFromAlbum(
                        resource,
                        session,
                        (top - len(results)),
                        usedUrls
                        ):
          
                        _addResult(result)

                else:
                    continue  
                

            return results



        except CaptchaDetected:
            retrys += 1
            if retrys > CAPTCHA_RETRIES:
                raise core.models.errors.TaskFailedError(
                    task="Bandcamp.search.solveCaptcha",
                    reason=f"CAPTCHA challenge persisted after {CAPTCHA_RETRIES} solving attempts",
                    caller="[providers] Bandcamp.search",
                    extraMessages=[
                        "OCR Captcha Handler couldn't solve required captcha for search",
                        "Please contact an admin to do it manually or try again"
                    ]
                )

            if _solveCaptcha(searchURL, session.cookieFile):
                session.reloadCookies()






def _getTrackResultsFromAlbum(
        album_resource: str,
        session: Session.Session,
        track_count: int,
        used_urls: set
        ) -> list[dict]:
    track_results: list[dict] = []

    albumUrlPattern: str = r'href="(https://[^"]+/album/[^"?]+)'
    try:
        albumUrl: str = core.general.DataSearch.searchBlocks(
            pattern=albumUrlPattern,
            search_block=album_resource,
            return_regex_exception=True
        )
    except core.models.errors.RegexSearchError:
    
        return []

    albumHtml: str = html.getHtml(
        session,
        url=albumUrl,
    )

    if not albumHtml:
        return []

    allTrackPattern = r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>'
    try:
        jsonDataRaw = core.general.DataSearch.searchBlocksAll(
            pattern=allTrackPattern,
            search_block=albumHtml,
            return_regex_exception=True
        )
    except core.models.errors.RegexSearchError:
        return []

   

    for x in jsonDataRaw:

        try:
            jsonData = json.loads(x)
            tracks = jsonData["track"]["itemListElement"]

        except (KeyError, TypeError, json.JSONDecodeError):
            continue
        

        for track in tracks:
            if len(track_results) >= track_count:
                break
    
            try:
                result = {
                    "thumbnail" : jsonData["image"],
                    "url" : track["item"]["@id"],
                    "title" : track["item"]["name"],
                    "type" : "track"
                }
            except (KeyError, IndexError, TypeError):
                continue

            if result["url"] in used_urls:
                continue
            
            track_results.append(result)
            
            
    return track_results




    

def _solveCaptcha(url: str, cookie_file: str) -> bool:
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
        try:
            solutions: list[str] = captcha_ocr.img_to_text(absolutePath, OCR_PATH, 5)
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
        
        return captchaBrowser.sendCaptchaSolutions(solutions)
    
    

    finally:
        if os.path.exists(tmpFile):
            os.remove(tmpFile)

        captchaBrowser.stop()

        
    



def _isClientChallenge(
        page_html: str
) -> bool:

    CLIENT_CHALLENGE_MARKERS = (
    "<title>Client Challenge</title>",
    "/_fs-ch-"
)
    
    if not isinstance(page_html, str):
        return False

    return any(marker in page_html for marker in CLIENT_CHALLENGE_MARKERS)





def _buildSearchUrl(
        search_term: str,
        search_filters: SearchFilters

) -> str:
    base_url = "https://bandcamp.com/search?"

    params = {
        "q": search_term
    }

    if search_filters.tags not in ([], ['']):
        tag_amount = len(search_filters.tags)

        if tag_amount > 1:
            raise core.models.errors.TaskFailedError(
                task="_buildSearchUrl",
                reason="Bancamp doesn't support multiple filter tags",
                caller="[providers] Bandcamp.search",
                extraMessages=[
                    f"Given amount of tags: '{tag_amount}'",
                    f"Given tags: {', '.join(search_filters.tags)}"
                ]
            )
        
        item_type = _reverseTypeMapping(search_filters.tags[0])
        if item_type is not None:
            params["item_type"] = item_type
        else:
            raise core.models.errors.TaskFailedError(
                task="_buildSearchUrl",
                reason="Invalid search filter was given",
                caller="[providers] Bandcamp.search",
                extraMessages=[
                    "Following filters are allowed: track, album, creator",
                    f"Given filter: '{search_filters.tags[0]}'"
                ]
            )


    searchURL = base_url + urllib.parse.urlencode(params)
    return searchURL






def _buildResult(
        track: str,
) -> dict | None:
    
    dictionary = {}
    try:
        thumbnail_pattern = r'<img\b[^>]*\bsrc="([^"]+)"'

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

        dictionary["type"] = "track"
    except core.models.errors.RegexSearchError:
        return None

    return dictionary





def _typeMapping(givenType: str) -> str | None:
    mapping = {
        "t": "track",
        "a": "album",
        "b": "creator"
    }
    return mapping.get(givenType, None)


def _reverseTypeMapping(tag) -> str | None:
    mapping = {
        "track" : "t",
        "album" : "a",
        "creator" : "b"
    }

    return mapping.get(tag, None)