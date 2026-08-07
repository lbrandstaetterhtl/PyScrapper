#Core Imports
from PythonModule.models.requests import SearchRequest
import PythonModule.core as core
from PythonModule.models import settings
from . import utils

#Python Default Imports
import asyncio



class SearchProcessor():
    def __init__(
            self,
            searchRequest: SearchRequest,
            session: core.request.Session.Session
            ):
        core.general.Validate.validateGeneralType(argument_name="searchRequest", obj=searchRequest, objType=SearchRequest, caller="[serverservices] SearchProcessor.init")
        core.general.Validate.validateSession(session=session, argument_name="session", caller="[serverservices] SearchProcessor.init")

        self.searchRequest: SearchRequest = searchRequest
        self.session = session



    async def run(self):
        provider:settings.ProviderTypes = utils.validateProviders(providerGiven=self.searchRequest.provider)
        results = {}

        searchFunction = settings.providerSearchMapping.get(provider, None)
        
        if searchFunction is None:
            raise Exception(f"Provider {self.searchRequest.provider} isn't supported for searching yet")
        
        results: dict = await asyncio.to_thread(
            searchFunction,
            search_term= self.searchRequest.search,
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

