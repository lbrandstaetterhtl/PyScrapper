

from PythonModule.core.network import Session
from PythonModule.models.requests import SearchFilters
import PythonModule.core as core
from PythonModule.core.network import html

#Python default imports
import urllib.parse

def search(
        search_term:str,
        filters: SearchFilters,
        session: Session,
        top:int = 5
        
        ) -> list[dict]:

    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term, caller="[providers] Youtube.search")
    core.general.Validate.special.validateSession(session=session, caller="[providers] Youtube.search")
    core.general.Validate.general.validateGeneralType(argument_name="filters", obj=filters, objType=SearchFilters, caller="[providers] Youtube.search")
    core.general.Validate.general.validateInt(argument_name="top", integer=top, caller="[providers] Youtube.search") 


    search_url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(search_term)


    searchHtml:str = html.getHtml(
        url=search_url,
        session=session
        )
    core.general.Validate.general.validateStr(argument_name="searchHtml", string=searchHtml, caller="[providers] Youtube.search.getHtml")
    
    
    keyword = "var ytInitialData = "

    jsondata: dict = core.general.DataSearch.searchJson(searchBlock=searchHtml, keyword=keyword)

   
    if not jsondata:
        raise core.models.errors.TaskFailedError(
            task="[CORE] searchJson",
            reason=f"Didn't find data with keyword {keyword}"
        )


    Data = []

    for videorenderer in core.general.DataSearch.iterValueFromJson(jsondata, "videoRenderer"):
        if not isinstance(videorenderer, dict):
            continue

        video = videorenderer.get("videoId")
        if not video:
            continue
        dictionary = {"identifier": video}
        


        if video:
            dictionary["url"] = "https://www.youtube.com/watch?v=" + video


        thumbnail = videorenderer.get("thumbnail", {}).get("thumbnails", [])
        if thumbnail:
            for obj in thumbnail:
                thumb_url = obj.get("url", None)
                if thumb_url:
                    dictionary["thumbnail"] = thumb_url
                    break
                
        
        title = videorenderer.get("title", {}).get("runs", [])
        if title:
            for obj in title:
                text = obj.get("text", None)
                if text:
                    dictionary["title"] = text
                    break


        Data.append(dictionary)


        if len(Data) == top:
            break


    return Data