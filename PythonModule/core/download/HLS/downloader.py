#Core Imports


from ...models.Download import DownloadContext
from ...models.errors import TaskFailedError
from ...network.Session import Session
from ...network import html


from ...general import DataSearch

#Python default imports
import asyncio





class HLSDownload():
    """
    Parent class for handling HLS downloads. It provides common functionality for both master and index HLS downloads, such as validating arguments and fetching HTML content.
    This class is not meant to be instantiated directly, but rather to be inherited by specific download classes like MasterHLSDownload and IndexHLSDownload.
    """
    def __init__(
            self,
            hls_url,
            session: Session,
            extra_headers: dict | None = None

            ):

#Validating every argument given
        self._validate_arguments(
            hls_url,
            session,
            extra_headers
        )
        

        self.extraHeaders: dict = extra_headers
        self.url: str = hls_url
        self.session = session if session is not None else Session()






#Gets used by index and master that's why parent function
#Also core.general.Html.getHtml doesn't return exceptions so we have to check each time if html was given
    def _get_html(
            self,
            given_url: str,
            variable_name: str,
            caller: str,
            extra_headers: dict | None = None,
            ) -> str:
        
        indexHtml: str = html.getHtml(
            session=self.session,
            url=given_url,
            extra_headers=extra_headers
        )

        if indexHtml is not None:
            return indexHtml

#If html wasn't None the function would return, but since it was None we know that something went wrong and we raise an Error
        raise TaskFailedError(
            task="[CORE] HLSDownload._get_html",
            reason="Html received was None",
            extraMessages=[
                f"URL: {given_url}",
                f"Used for variable: {variable_name}"
            ],
            caller=caller
        )
        
        


#HLS Download class is the public "api", this function checks every argument if it is correct and valid
    def _validate_arguments(
            self,
            hls_url: str,
            session: Session,
            extra_headers: dict | None = None
            ):

        from ...general import Validate

        Validate.special.validateHostDefault(
            url=hls_url,
            caller="[CORE] HLSDownload.init"
        )
       
        Validate.special.validateSession(
                session, argument_name="session", caller="[CORE] HLSDownload.init"
            )

        if extra_headers:
            Validate.general.validateDict(
                argument_name="extra_headers",
                dictionary=extra_headers,
                caller="[CORE] HLSDownload.init"
            )


    

        
