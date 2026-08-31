#Core Imports
from ..models.errors import RegexSearchError,  TaskFailedError
from ..general import Validate

#Python default Imports
import re
import json



#Functions

#This functions searches an given string for a regex pattern and returns the first match, if no match is found it raises a RegexSearchError
def searchBlocks(
        pattern: str,
        search_block: str,
        return_regex_exception:bool = False
) -> str:

    _validateArguments_SearchBlocks(pattern, search_block, return_regex_exception, caller="[CORE] searchBlocks")
    match = re.search(pattern, search_block, re.DOTALL)

    if match:
        result_block = match.group(1).strip()
        return result_block
    else:
        
        if return_regex_exception == True:
            raise RegexSearchError(
                pattern=pattern,
                searchBlock=search_block
            )
        return ""
    


        
        
    


#This functions searches an given string for a regex pattern and returns all matches, if no match is found it raises a RegexSearchError
def searchBlocksAll(
        pattern: str,
        search_block: str,
        return_regex_exception: bool = False
) -> list:
    
    _validateArguments_SearchBlocks(pattern, search_block, return_regex_exception, caller="[CORE] searchblocksAll")

    matches = re.findall(pattern, search_block, re.DOTALL)

    if not matches:
        if return_regex_exception == True:
            raise RegexSearchError(
            pattern=pattern,
            searchBlock=search_block
            )
        else: return ""
    
    for match in matches:
        if isinstance(match, str):
            match = match.strip()
    return matches




def searchJson(
        searchBlock: str,
        keyword: str,
        return_regex_exception: bool = False
        ) -> dict:



    found = searchBlocks(pattern=keyword + r"({.*?});", search_block=searchBlock, return_regex_exception=return_regex_exception)

    if not found:
        raise TaskFailedError(
            task="searchBlocks",
            reason=f"Couldn't find object with given keyword {keyword}",
            caller="[CORE] searchJson",
        )

       
    jsondata = json.loads(found)

    return jsondata



def iterValueFromJson(
        data: dict,
        value: str
):
    if isinstance(data, dict):
        if value in data:
            yield data[value]

        for key in data:
            yield from iterValueFromJson(data[key], value)


    elif isinstance(data, list):
        for item in data:
            yield from iterValueFromJson(item, value)





def _validateArguments_SearchBlocks(
    pattern: str,
    search_block: str,
    return_exception: bool,
    caller: str
):
    Validate.general.validateStr(argument_name="pattern", string=pattern, caller=caller)
    Validate.general.validateStr(argument_name="search_block", string=search_block, caller=caller)
    Validate.general.validateBool(argument_name="return_regex_exception", boolean=return_exception, caller=caller)