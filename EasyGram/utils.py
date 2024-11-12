from typing import Union

def CheckDict(_obj: dict, _key: str) -> Union[dict, bool]:
    try:
        _dict = _obj[_key]
        return _dict
    except KeyError:
        return False
    except TypeError:
        return False