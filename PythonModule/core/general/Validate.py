#Core Imports
from ..models.errors import ArgumentError, InvalidURLError, TaskFailedError
from ..models.Settings import VALID_ENCODINGS, VALID_URLLIBREQUEST_METHODS


#Python Default imports
import re
import os
import urllib.parse, urllib.request
import ipaddress
import asyncio


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
    
    validateRequestMethod(method=request.method, caller=caller)

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



def validateDict(
        argument_name: str,
        dictionary: dict,
        caller: str = "[CORE] validateDict"
):
    if (
        not dictionary
        or not isinstance(dictionary, dict)
    ):
        raise ArgumentError(
            argument=argument_name,
            wanted_type="dict",
            caller=caller,
            obj=dictionary
        )



def validateStr(
        argument_name: str,
        string: str,
        caller: str = "[CORE] validateStr"
):
    if (
        not string
        or not isinstance(string, str)
        or not string.strip()
    ):
        raise ArgumentError(
            argument=argument_name,
            wanted_type="str",
            caller=caller,
            obj=string
        )

def validateInt(
        argument_name : str,
        integer: int,
        caller: str = "[CORE] validateInt"
):
    if (
        not integer
        or not isinstance(integer, int)
        or not integer > 0
    ):
        raise ArgumentError(
            argument=argument_name,
            wanted_type="int > 0",
            caller=caller,
            obj=integer
        )

def validateListStr(
        argument_name: str,
        liste: list[str],
        caller: str = "[CORE] validateListStr"
):
    if (
        not liste
        or not isinstance(liste, list)
        or not all(isinstance(item, str) or item.strip() for item in liste)
    ):
        raise ArgumentError(
            argument=argument_name,
            wanted_type="list[str]",
            caller = caller,
            obj=liste
        )


def validateSession(
        session, 
        argument_name = "session",
        caller: str = "[CORE] validateSession"
):
    from ..request.Session import Session
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

def validateBool(
        boolean: bool,
        argument_name: str,
        caller: str = "[CORE] validateBool"
):
    if not isinstance(boolean, bool):
 
        raise ArgumentError(
            caller=caller,
            argument=argument_name,
            wanted_type="bool",
            obj=boolean
        )

def validateOutFile(
    out_file: str,
    caller: str = "[CORE] validateOutFile"
):
    validateStr(argument_name="out_file", string=out_file, caller=caller)
    try:
        path = os.path.abspath(out_file)
        invalidReasonList: list[str] = []
        if "\0" in path:
            invalidReasonList.append("Null Byte was found, this makes the path invalid")
        if os.path.exists(out_file):
            invalidReasonList.append("Given outFile already exists. Please choose another outFile")

        parent = os.path.dirname(os.path.abspath(out_file))
        os.makedirs(parent, exist_ok=True)

        os.stat(os.path.dirname(path) or ".")

        
        

        if invalidReasonList:
            raise TaskFailedError(
                task=f"validateOutFile '{out_file}'",
                reason=f"{', '.join(invalidReasonList)}",
                caller=caller
            )

    except Exception as e:
        raise TaskFailedError(
            task=f"validateOutFile {out_file}",
            reason=str(e),
            caller=caller
        )

def validateGeneralType(
    argument_name: str,
    obj,
    objType: type,
    caller: str = "[CORE] validateGeneralType",

):
    if (
        not obj
        or not isinstance(obj, objType)
    ):
        raise ArgumentError(
            argument=argument_name,
            wanted_type=f"{objType}",
            obj=obj,
            caller=caller,
        )

def validateDownloadInformation(
    argument_name: str,
    download_information,
    caller: str  = "[CORE] validateDownloadInformation"
):
    from ..models.General import DownloadInformations
    if (
        not download_information
        or not isinstance(download_information, DownloadInformations)
    ):
        raise ArgumentError(
            argument=argument_name,
            wanted_type="core.models.General.DownloadInformations",
            obj=download_information,
            caller=caller
        )
    if (
        not download_information.downloadLimiter
        or not isinstance(download_information.downloadLimiter, asyncio.Semaphore)
    ):
        raise ArgumentError(
            argument=f"{argument_name}.downloadLimiter",
            wanted_type="asyncio.Semaphore",
            obj=download_information.downloadLimiter,
            caller=caller
        )
    
    validateSession(session=download_information.session, argument_name=argument_name, caller=caller)
    validateOutFile(out_file=download_information.outFile, caller=caller)
    validateDict(argument_name=f"{argument_name}.downloadProgress", dictionary=download_information.downloadProgress)
    validateHostDefault(url=download_information.url, caller=caller)
   