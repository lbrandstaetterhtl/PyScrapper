#Imports
import re
from ..models.errors import RegexSearchError
import json

#Functions

#This functions searches an given string for a regex pattern and returns the first match, if no match is found it raises a RegexSearchError
def searchBlocks(
        pattern: str,
        searchBlock: str,
        returnException:bool = False
) -> str:
    if not isinstance(pattern, str): raise ValueError("searchBlocks: given pattern is not a string")
    if not isinstance(searchBlock, str): raise ValueError("searchBlocks: given search block is not a string")
    match = re.search(pattern, searchBlock, re.DOTALL)

    if match:
        result_block = match.group(1).strip()
        return result_block
    else:
        
        if returnException == True:
            raise RegexSearchError(
                pattern=pattern,
                searchBlock=searchBlock
            )
        return ""
    



#This functions searches an given string for a regex pattern and returns all matches, if no match is found it raises a RegexSearchError
def searchBlocksAll(
        pattern: str,
        searchBlock: str,
        returnException: bool = False
) -> list:
    
    if not isinstance(pattern, str): raise ValueError("searchBlocksAll: given pattern is not a string")
    if not isinstance(searchBlock, str): raise ValueError("searchBlocksAll: given search block is not a string")


    matches = re.findall(pattern, searchBlock, re.DOTALL)

    if not matches:
        if returnException == True:
            raise RegexSearchError(
            pattern=pattern,
            searchBlock=searchBlock
            )
        else: return ""
    
    for match in matches:
        if isinstance(match, str):
            match = match.strip()
    return matches




def searchJson(
        searchBlock: str,
        keyword: str
        ) -> dict:
    if not isinstance(searchBlock, str): raise ValueError("searchJson: given block to search isn't a string")
    if not isinstance(keyword, str): raise ValueError("searchJson: given keyword isn't a string")

    found = re.search(keyword + r"({.*?});", searchBlock, re.DOTALL)

    if not found:
        raise Exception("searchJson: Failed to find the json data")
    
    try:    
        jsondata = json.loads(found.group(1))

    except json.JSONDecodeError:
        raise Exception("searchJson: Failed to decode the JSON data")


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