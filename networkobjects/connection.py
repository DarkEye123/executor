import copy

from command import Command
from executor_exceptions import *
from host import Host
from network_object import NetworkObject
from . import logger
from .user import User

__author__ = 'mlesko'


# Please be sure you are creating Connection object only via provided executor API
class Connection(NetworkObject):
    """
    Class representing a connection with associated data to the transfer.
    This class should'nt be instantiated manually but only via L{dtestlib.executor.executor.Executor}.

    Every connection is unique and specified by its user and host. If there is an attempt to create
    the connection with the same identifier as already exists, this existing connection is returned.

    For more info about possibilities see L{NetworkObject}.

    Connection class supports comparison by '=='
    """

    def __new__(cls, host=None, user=None, client=None):
        """
        If connection already exists (id is combination host & user), the existing one is returned.
        @param host: host object representing a place where a connection is going to be made.
        @type host: Host
        @param user: user object represents a credentials used during the authorization and authentication.
        @type user: User
        @param client: underlying client which is used by the model of the executor
        @type client: any
        @return: connection (empty)
        @rtype: Connection
        """
        cls.__check_parameters(host=host, user=user)
        if client is None:
            raise InvalidClientException("Integrated Client during connection creation can't be None")
        return super(Connection, cls).__new__(cls, host=host, user=user, client=client)

    def __init__(self, host=None, user=None, client=None):
        """
        If connection already exists (id is combination host & user), the initialization is skipped.
        @param host: host object representing a place where a connection is going to be made.
        @type host: Host
        @param user: user object represents a credentials used during the authorization and authentication.
        @type user: User
        @param client: underlying client which is used by the model of the executor
        @type client: any
        @return: connection (empty)
        @rtype: Connection
        """
        _id = Connection.generate_id(host, user)  # do init only if it is new object
        if not hasattr(Connection, "__pool__") or not Connection.__pool__.has_key(_id):
            self.host = host
            self.user = user
            self.id = _id
            user.connections.add(self)
            host.connections.add(self)
            self.client = client
            self.__available_results = []
            self.incomplete_results = []  # TODO no linked lists anywhere, write your own
            # execute, execute batch and close methods need to be mapped after object creation from the outside
            self._execute_fn = None
            self._execute_batch_fn = None
            self._close_f = None
            self._connect = None
            self.connected = False
            super(Connection, self).__init__(self.id)
            logger.debug('Created %s' % self)

    def __str__(self):
        return "%s object: %s" % (self.__class__.__name__, self.id)

    def __eq__(self, other):
        if not isinstance(other, Connection):
            return False
        if self.id != other.id:
            return False
        return True

    @classmethod
    def __check_parameters(cls, host, user):  # client is not checked here, because he is assigned on 1 place only
        if not isinstance(host, Host):
            raise InvalidHostException("host must be instance of %s class" % Host)
        if not isinstance(user, User):
            raise InvalidUserException("user must be instance of %s class" % User)

    @classmethod
    def find(cls, host, user):
        """
        Lookout for connection in the underlying container and return it.
        Every connection has its id by host & user
        @type host: Host
        @type user: User
        @return: connection object or none
        @rtype: Connection|None
        """
        cls.__check_parameters(host=host, user=user)
        if not hasattr(Connection, "__pool__"):
            return None
        cid = cls.generate_id(host, user)
        return Connection.__pool__.get(cid)  # by default None is returned

    @classmethod
    def generate_id(cls, host, user):
        """
        Generate id for connection consisting from user and host object.
        @type host: Host
        @type user: User
        @return: generated id
        @rtype: str
        """
        cls.__check_parameters(host=host, user=user)
        return Connection._generate_id(host=host, user=user)

    @classmethod
    def _generate_id(cls, *args, **kwargs):
        """
        Use L{generate_id} instead.
        """
        if args != () or kwargs != {}:
            if kwargs != {}:
                host = kwargs.get("host")  # "or" is not used here due to possible None value in dict
                user = kwargs.get("user")
            elif args != ():
                host = args[0]
                user = args[1]
            return "%s@%s:%s" % (user.username, host.address, host.port)

    def _close(self):  # used by model_tests
        """
        This is extremely important function and should be used directly by the model_tests,
        user should not coll it directly.
        """
        Connection.__pool__.pop(self.id)
        self.connected = False

    def close(self):
        """
        Mapped function. Functionality is provided by the model.
        @raise MissingFunctionDefinition: if close method was not mapped.
        """
        if self._close_f is None:
            raise MissingFunctionDefinition("Close method is not mapped")
        self._close_f()

    def connect(self):
        """
        Mapped function. Functionality is provided by the model.
        @raise MissingFunctionDefinition: if connect method was not mapped.
        """
        if self._connect is None:
            raise MissingFunctionDefinition("connect method is not mapped")
        if not self.connected:
            self._connect()

    def get_available_results(self):
        """
        Connections are able to have many separate commands executed. After the command execution a result object is made.
        This method provides a way how to provide all already finished results from the connection class to the programmer.
        @return: list of results L{ExecResult}
        @rtype: list
        """
        to_move = []

        for res in self.incomplete_results:
            if res.result_available:  # TODO possibly usage of semaphores here
                to_move.append(res)

        # could be used as one-liner, but this is in place removing, which is faster when subset to remove is small
        # which will be the case most of the time
        for res in to_move:
            self.incomplete_results.remove(res)

        self.__available_results.extend(to_move)

        return copy.copy(self.__available_results)

    def execute(self, command):
        """
        Execute given command on the connection. This method
        needs to be mapped by the model.
        @param command: command to be executed
        @type command: basestring | Command
        @return: result of the execution
        @rtype: ExecResult
        @raise InvalidCommandValue: if command is not the L{Command} instance or an instance of the string
        @raise MissingFunctionDefinition: if execute method was not mapped.
        """
        if not (isinstance(command, basestring) or isinstance(command, Command)):
            raise InvalidCommandValue("cmd must be a string or an instance of the Command class")
        if self._execute_fn is None:
            raise MissingFunctionDefinition("Execute method is not mapped")
        return self._execute_fn(command)

    def execute_batch(self, commands=()):
        """
        Execute a batch of commands. This method
        needs to be mapped by the model.
        @param commands: list of commands. Command can be string or an instance of the class L{Command}
        @type commands: list | tuple
        @return: list of results of the type L{ExecResult}
        @rtype: list
        @raise InvalidCommandValue: if commands are not iterable or the content of the list is not executable
        @raise MissingFunctionDefinition: if execute_batch method was not mapped.
        """
        if not hasattr(commands, "__iter__"):
            raise InvalidCommandValue("commands must be an iterable")
        if self._execute_batch_fn is None:
            raise MissingFunctionDefinition("execute_batch method is not mapped")
        return self._execute_batch_fn(commands)
