
from PythonModule.core.network import Session
from PythonModule.models.requests import SearchFilters
import PythonModule.core.general as core
from PythonModule.core.network import html
from PythonModule.core.network import EmergencyBrowser
import PythonModule.core as core

#Python default imports
import urllib.parse
import json
import re

def searchMusic(
    search_term:str,
    filters: SearchFilters,
    session: Session,
    top:int = 5
    
    ) -> list[dict]:

    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term, caller="[providers] Youtube.searchMusic")
    core.general.Validate.special.validateSession(session=session, caller="[providers] Youtube.searchMusic")
    core.general.Validate.general.validateGeneralType(argument_name="filters", obj=filters, objType=SearchFilters, caller="[providers] Youtube.searchMusic")
    core.general.Validate.general.validateInt(argument_name="top", integer=top, caller="[providers] Youtube.searchMusic") 

    searchUrl: str = "https://music.youtube.com/search?q=" + urllib.parse.quote(search_term)

    searchHtml = html.getHtml(session=session, url=searchUrl)

    if "consent" in searchHtml:
        EmergencyBrowser.BrowserButtonPress(
            url=searchUrl,
            button_name="",
            headless=False,
            wait_before_click_ms=2000,
            wait_after_click_ms=2000
        )
        session.reloadCookies()
        searchHtml = html.getHtml(session=session, url=searchUrl)

    pattern = (
    r"initialData\.push\(\{"
    r"path: '\\/search',"
    r".*?"
    r"data: '((?:\\.|[^'])*)'"
    r"\}\);"
)
    encodedJson = core.general.DataSearch.searchBlocks(pattern, searchHtml, True)
    decodedJson = re.sub(
        r"\\x([0-9a-fA-F]{2})",
        lambda m: chr(int(m.group(1), 16)),
        encodedJson
    )

    decodedJson = decodedJson.replace(r'\\"', r'\"')

    results: list[dict] = []

    
    jsondata = json.loads(decodedJson)



    for renderer in core.general.DataSearch.iterValueFromJson(
        jsondata,
        "musicCardShelfRenderer"
    ):
        if len(results) >= top:
            break
        try:
            titleRun = renderer["title"]["runs"][0]

            title = titleRun["text"]
            videoId = (
                titleRun["navigationEndpoint"]
                ["watchEndpoint"]
                ["videoId"]
            )

            thumbnail = (
                renderer["thumbnail"]
                ["musicThumbnailRenderer"]
                ["thumbnail"]
                ["thumbnails"][-1]
                ["url"]
            )

        except (KeyError, IndexError, TypeError):
            continue

        results.append({
            "identifier": videoId,
            "url": f"https://music.youtube.com/watch?v={videoId}",
            "title": title,
            "thumbnail": thumbnail,
        })

    

    for musicRenderer in core.general.DataSearch.iterValueFromJson(jsondata, "musicResponsiveListItemRenderer"):
        if len(results) >= top:
            break
        try:
            idk = (
                musicRenderer["flexColumns"][0]
                ["musicResponsiveListItemFlexColumnRenderer"]
                ["text"]
                ["runs"][0]
            )
            title = idk["text"]

            thumbnail = (
            musicRenderer["thumbnail"]
            ["musicThumbnailRenderer"]
            ["thumbnail"]
            ["thumbnails"][-1]
            ["url"]
        )

            videoId = (
            idk["navigationEndpoint"]
            ["watchEndpoint"]
            ["videoId"]
        )

            

        except (KeyError, IndexError, TypeError):
            continue

        result = {
            "identifier" : videoId,
            "url" : f"https://music.youtube.com/watch?v={videoId}",
            "title" : title,
            "thumbnail" : thumbnail
        }

        results.append(result)

    return results