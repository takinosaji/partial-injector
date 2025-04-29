import traceback

class PartialContainerException(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

def get_excp_dict_or_msg(e: BaseException) -> dict | str:
    return e.args[0] if isinstance(e.args[0], dict) else e

def get_stacktrace() -> str:
    return  traceback.format_exc()