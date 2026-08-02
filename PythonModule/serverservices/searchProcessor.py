from PythonModule.models.requests import SearchRequest
from PythonModule.core.request.Session import Session
from PythonModule.models import processorModels 
from . import utils
import asyncio



class SearchProcessor():
    def __init__(
            self,
            searchRequest: SearchRequest,
            session: Session
            ):
        if not isinstance(searchRequest, SearchRequest): raise ValueError("[ERROR] SearchProcessor: searchRequest must be from type 'SearchRequest'")

        if not isinstance(session, Session): raise ValueError("[ERROR] SearchProcessor: session given musst be from class 'Session'")

        if not isinstance(searchRequest.top, int) or searchRequest.top < 0:
            raise ValueError("[ERROR] SearchProcessor: Top results given must be an integer above 0")

        self.searchRequest: SearchRequest = searchRequest
        self.session: Session = session



    async def run(self):
        provider:processorModels.ProviderTypes = utils.validateProviders(providerGiven=self.searchRequest.provider)
        results = {}

        searchFunction = processorModels.providerSearchMapping.get(provider, None)
        if searchFunction is None:
            raise Exception(f"Provider {self.searchRequest.provider} isn't supported for searching yet")
        
        results: dict = await asyncio.to_thread(
            searchFunction,
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

