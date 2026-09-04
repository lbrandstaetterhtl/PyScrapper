import PythonModule
from PythonModule.core.network import Session
ses = Session.Session()
providerRequest = PythonModule.providers.models.ProviderResultRequest(
    url="https://www.youtube.com/watch?v=G9ntpmqSAmI",
    ses=ses,
    
)

PythonModule.providers.Youtube.getMediaInformation(
    request=providerRequest
)