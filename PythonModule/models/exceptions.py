class PyScrapperError(Exception): ...

class InvalidMediaType(Exception): 
    def __init__(
            self,
            mediatype: str,
            provider: str,
            supported:list
            ):
        
        self.provider:str = provider
        self.supported:list = supported

        exceptionsMessage = (
            f"Given mediatype '{mediatype}' is invalid for provider '{provider}'."
            f"Supported mediatypes: {', '.join(supported)}"
        )

        super().__init__(exceptionsMessage)



class NotSupportedProvider(Exception):
    def __init__(
            self,
            provider:str,
            supported:list
            ):
        exceptionMessage = (
            f"Given provider '{provider}' is not supported."
            f"Supported providers: {', '.join(supported)}"
        )
        super().__init__(exceptionMessage)



class InvalidURL(Exception):
    def __init__(
            self,
            url: str,
            reason: str
            ):
        exceptionMessage = (
            f"Given url {url} was invalid"
            f"Invalid because of the following reason {reason}"
        )
        super().__init__(exceptionMessage)



class CommandError(Exception):
    def __init__(
            self,
            command:str,
            supported:list
    ):
        exceptionMessage = (
            f"Given command {command} does not exist"
            f"Following commands are valid {', '.join(supported)}"

        )
        super().__init__(exceptionMessage)
    
    