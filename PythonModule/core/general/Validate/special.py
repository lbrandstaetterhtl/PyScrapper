#Core imports
from ...models.errors import ArgumentError, InvalidURLError
from ...models.Settings import VALID_ENCODINGS, VALID_URLLIBREQUEST_METHODS

#Own imports
from .general import validateStr, validateListStr

#Python Default imports
import urllib.parse, urllib.request
import ipaddress
import re



ALLOWED_FILE_OPEN_METHOD = [
"r",
"rb",
"r+",
"rb+",

"w",
"wb",
"w+",
"wb+",

"x",
"xb",
"x+",
"xb+",

"a",
"ab",
"a+",
"ab+",
]

def validateHostDefault(
        url: str,
        caller: str = "[CORE] validateHostDefault"
) -> bool:

    validateStr(argument_name="url", string=url, caller=caller)
    
   


    invalidReasonList: list[str] = []


    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname


#Allow IP adresses
    try:
        ipaddress.ip_address(hostname)
        return
    
    except ValueError:
        pass

#Checking length of the dns name
    if len(parsed.hostname) > 253:
        invalidReasonList.append("DNS name is too long. Allowed length: 254")


    if hostname.endswith("."):
        hostname = hostname[-1]

#Splitting every label of hostname for example www.newgrounds.com -> ["www", "newgrounds", "com"]
    labels = hostname.split(".")

    if len(labels) < 2:
        invalidReasonList.append("Hostname needs atleast two labels.")

    labelPattern = re.compile(
        r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
    )

#Now checking every label if their they have valid number or letter in it
    if not all(labelPattern.fullmatch(label) for label in labels):
        invalidReasonList.append("Invalid numbers and letters found in hostname.")

    if invalidReasonList:
        raise InvalidURLError(
            caller=caller,
            url=url,
            reasonList=invalidReasonList
        )

    
def validateUrllibRequest(
    request: urllib.request.Request,
    argument_name: str = "request",
    caller: str = "[CORE] validateUrllibRequest"
):
    if not isinstance(request, urllib.request.Request):
            raise ArgumentError(
                caller=caller,
                argument=argument_name,
                wanted_type="urllib.request.Request"
            )
        
    elif (
        not request.full_url
        or not isinstance(request.full_url, str) or not request.full_url.strip()
    ):
        raise ArgumentError(
            caller="[CORE] loadJSONUrl",
            argument=f"{argument_name}.full_url",
            wanted_type="str"
        )
    
    validateRequestMethod(method=request.get_method(), caller=caller)

def validateRequestMethod(
        method: str,
        caller: str = "[CORE] validateRequestMethod"
): 
   
    if (  
        not method
        or not isinstance(method, str) or not method.strip()
        or method.upper() not in VALID_URLLIBREQUEST_METHODS
    ):
        raise ArgumentError(
            argument="request.method",
            wanted_type=f"str: Allowed method -> {', '.join(VALID_URLLIBREQUEST_METHODS)}",
            caller=caller,
            obj=method

        )



def validateHostPro(
        
        url: str,
        allowed_protocols_list: list[str] = ["https"],
        allowed_hostnames_list: list[str] = None,
        caller: str = None,
) -> bool:
    
    if not caller or type(caller) is not str:
        caller = "[CORE] validateHostPro"

    validateListStr("allowed_hostnames_list", liste=allowed_hostnames_list, caller="[CORE] validateHostPro")
    validateListStr("allowed_protocols_list", liste=allowed_protocols_list, caller="[CORE] validateHostPro")
    validateHostDefault(url)
    
   

    invalidReasonList: list[str] = []

    parsedUrl = urllib.parse.urlparse(url.lower())

#Scheme gives us the protocol
    if parsedUrl.scheme not in allowed_protocols_list:
        invalidReasonList.append(f"URL doesn't use allowed protocol. Allowed protocols: {', '.join(allowed_protocols_list)} ")

    if parsedUrl.hostname not in allowed_hostnames_list:
        invalidReasonList.append(f"URL hostname isn't a valid host. Valid hosts: {', '.join(allowed_hostnames_list)}")

    if invalidReasonList:
        raise InvalidURLError(
            caller=caller,
            url=url,
            reasonList=invalidReasonList
        )






def validateSession(
        session, 
        argument_name = "session",
        caller: str = "[CORE] validateSession"
):
    from ...network.Session import Session
    if (
        not session
        or not isinstance(session, Session)
    ):
        raise ArgumentError(
            argument=argument_name,
            wanted_type="core.request.Session.Session",
            caller=caller,
            obj=session
        )

def validateEncoding(
    encoding: str,
    argument_name: str = "encoding",
    caller: str = "[CORE] validateEncoding"
):
    if (
            not isinstance(encoding, str)
            or not encoding in VALID_ENCODINGS
        ):
            raise ArgumentError(
                caller=caller,
                argument=argument_name,
                wanted_type=f"str: {', '.join(VALID_ENCODINGS)}",
                obj=encoding
            )


def validateFileOpen(
        open_method: str,
        arugment_name: str = "file_open_method",
        caller: str = "[CORE] validateFileOpen"
): 
    if (
        not open_method
        or not isinstance(open_method, str)
        or not open_method in ALLOWED_FILE_OPEN_METHOD
    ):
        raise ArgumentError(
            argument=arugment_name,
            wanted_type="normal file open method",
            obj=open_method,
            caller=caller
        )
    