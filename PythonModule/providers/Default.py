# Core Imports
import PythonModule.core as core
from PythonModule.core.network import EmergencyBrowser

from . import models

#Python Default Imports








def getMediaInformation(
        request: models.ProviderResultRequest,
) -> models.ProviderResult:

    
   

    
    medialist: core.models.media.MediaList = EmergencyBrowser.BrowserDiscoverStreamURLs(
            url = request.url,
            ad_block=True,
            headless=True,
            extra_headers=request.extra_headers
        )
    


    if not medialist:
        raise core.models.errors.TaskFailedError(
            task="BrowserDiscoverStreamURLs",
            reason="Browser isn't currently capable of finding medias on given url",
            extraMessages=[f"Given url: {request.url}"]
        )

    bestCandidate = medialist.candidates[0]
    return models.makeProviderResultFromCandidate(bestCandidate)
    
    

#Penis
    



