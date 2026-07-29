
from PythonModule.providers import Youtube, Suno, Archive, Bandcamp
from PythonModule.models.requests import SearchRequest
from PythonModule.core.request.Session import Session
from . import utils
import asyncio


class SearchProcessor():
    def __init__(
            self,
            searchRequest: SearchRequest,
            session: Session
            ):
        if not isinstance(searchRequest, SearchRequest): raise ValueError("searchRequest must be from type 'SearchRequest'")

        if not isinstance(session, Session): raise ValueError("session given musst be from class 'Session'")

        if not isinstance(searchRequest.top, int) or searchRequest.top < 0:
            raise ValueError("top results given must be an integer above 0")

        self.searchRequest: SearchRequest = searchRequest
        self.session: Session = session



    async def run(self):
        provider = utils.validateProviders(providerGiven=self.searchRequest.provider)
        if not provider: 
            raise ValueError("No supported provider was given")
        if provider == "archive":
            results = await asyncio.to_thread(
                Archive.search,
                search= self.searchRequest.search,
                session=self.session,
                top=self.searchRequest.top
            )
        elif provider == "youtube":
            results = await asyncio.to_thread(
                Youtube.search,
                search= self.searchRequest.search,
                session=self.session,
                top=self.searchRequest.top
            )

        elif provider == "suno":
            results = {}

            
        elif provider == "bandcamp":
            results = await asyncio.to_thread(
                Bandcamp.search,
                search= self.searchRequest.search,
                filters = self.searchRequest.filters,
                session = self.session,
                top = self.searchRequest.top
            )

        response = {
                    "provider": self.searchRequest.provider,
                    "query": self.searchRequest.search,
                    "results": results
                }
        return response

