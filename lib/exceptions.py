"""
Contains all Exceptions class
"""


class ExecutionError(Exception):
    """
    Raise Execution_Error Exception
    """
    pass


class InvalidArgument(Exception):
    """
    Raise Invalid_Argument Exception
    """
    pass


class AlreadyExist(Exception):
    """
    Raise Already_Exist Exception
    """
    pass

class UserException(Exception):
    '''
    Raise exception when user did not provide valid options.
    '''
    pass

class EnvException(ExecutionError):
    pass

class TMDBException(ExecutionError):
    pass

class TestBuildTypeException(ExecutionError):
    pass
