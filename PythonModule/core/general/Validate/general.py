#Core imports

from ...models.errors import ArgumentError

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