__author__ = 'mlesko'


class ExecutorException(Exception):
    pass


# ************** No-Category Exceptions **************
class InvalidClientException(ExecutorException):
    pass


class InvalidChannelException(ExecutorException):
    pass


class MissingDefinitionException(ExecutorException):
    pass


class NotImplementedError(ExecutorException):
    pass


# ************** Connection's Exceptions **************
class ConnectionException(ExecutorException):
    pass


class ConnectionNotFound(ConnectionException):
    pass


class ConnectionCloseError(ConnectionException):
    pass


class InvalidConnection(ConnectionException):
    pass


# ************** Command's Exceptions **************
class CommandException(ExecutorException):
    pass


class InvalidCommandValue(CommandException):
    pass


# ************** Host's Exceptions **************
class HostException(ExecutorException):
    pass


class InvalidHostException(HostException):
    pass


class InvalidAddress(HostException):
    pass


class InvalidPortValue(HostException):
    pass


# ************** User's Exceptions **************
class UserException(ExecutorException):
    pass


class InvalidUserException(UserException):
    pass


class InvalidUsernameExeption(UserException):
    pass


# ************** Model's Exceptions **************
class ModelException(ExecutorException):
    pass


class InvalidModelException(ModelException):
    pass


# ************** Result's Exceptions **************
class MissingFunctionDefinition(MissingDefinitionException):
    pass
