from __future__ import absolute_import

import signal

from metaclasses.singleton_wrapper import SingletonWrapper
from models.paramiko_model import ParamikoModel
from models.remote_execution_template import RemoteExecutionTemplate
from networkobjects.connection import Connection
from networkobjects.host import Host
from networkobjects.user import User
from executor_exceptions import InvalidModelException

__author__ = 'mlesko'
__all_ = ['Executor']


class Executor(object):
    __metaclass__ = SingletonWrapper
    active_connection = None

    def __init__(self, model=ParamikoModel):
        if model is None or not issubclass(model, RemoteExecutionTemplate):
            raise InvalidModelException("model must be an instance of RemoteExecutionTemplate")

        self.model = model()

    @property
    def active_connection(self):
        return self.model.__class__.active_connection

    @active_connection.setter
    def active_connection(self, connection):
        self.model.__class__.active_connection = self.model._set_connection(connection)

    def iter_connections(self):
        """
        Iterate over all available connections
        @return: iterator to the connection
        @rtype: iterator to L{dtestlib.executor.networkobjects_tests.connection.Connection}
        """
        return iter(Connection)

    def iter_hosts(self):
        """
        Iterate over all available hosts
        @return: iterator to the host
        @rtype: iterator to L{dtestlib.executor.networkobjects_tests.host.Host}
        """
        return iter(Host)

    def iter_users(self):
        """
        Iterate over all available users
        @return: iterator to the user
        @rtype: iterator to L{dtestlib.executor.networkobjects_tests.user.User}
        """
        return iter(User)

    def create_command(self, command):
        """
        Creates a command object.
        @param command: command to execute
        @type command: str
        @return: command object
        @rtype: L{dtestlib.executor.dataobjects.command.Command}
        """
        return self.model.create_command(command=command)

    def execute(self, command=None, connection=None):
        """
        Executes command on the connection
        @param command: command to execute
        @type command: str or L{dtestlib.executor.dataobjects.command.Command}
        @param connection: a connection on which command will be executed
        @type connection: L{dtestlib.executor.networkobjects_tests.connection.Connection}
        @return: result object with provided API
        @rtype:L{dtestlib.executor.networkobjects_tests.exec_result.ExecResult}
        """
        return self.model.execute(command=command, connection=connection)

    def execute_wait(self, command=None, connection=None):
        """
        Executes command on the connection and waits for its completion
        @param command: command to execute
        @type command: str or L{dtestlib.executor.dataobjects.command.Command}
        @param connection: a connection on which command will be executed
        @type connection: L{dtestlib.executor.networkobjects_tests.connection.Connection}
        @return: result object with provided API
        @rtype:L{dtestlib.executor.networkobjects_tests.exec_result.ExecResult}
        """
        result = self.model.execute(command=command, connection=connection)
        result.wait_for_data()
        return result

    def execute_batch(self, commands=(), connection=None):
        """
        Executes a set of commands on the connection
        @param command: A set of commands to be executed
        @type command: iterable
        @param connection: a connection on which command will be executed
        @type connection: L{dtestlib.executor.networkobjects_tests.connection.Connection}
        @return: list of result objects with provided API
        @rtype: list
        """
        return self.model.execute_batch(commands=commands, connection=connection)

    def execute_batch_wait(self, commands=(), connection=None):
        """
        Executes a set of commands on the connection and waits for their completion
        @param command: A set of commands to be executed
        @type command: iterable
        @param connection: a connection on which command will be executed
        @type connection: L{dtestlib.executor.networkobjects_tests.connection.Connection}
        @return: list of result objects with provided API
        @rtype: list
        """
        results = self.model.execute_batch(commands=commands, connection=connection)
        self.wait(results)
        return results

    def execute_everywhere(self, command=None):
        """
        Executes command on every available connection
        @param command: command to execute
        @type command: str or L{dtestlib.executor.dataobjects.command.Command}
        @return: list of result objects L{dtestlib.executor.networkobjects_tests.exec_result.ExecResult} with provided API
        @rtype: list
        """
        res_list = []
        for connection in Connection:
            result = self.model.execute(command=command, connection=connection)
            res_list.append(result)
        return res_list

    def execute_everywhere_wait(self, command=None):
        """
        Executes command on every available connection and wait
        @param command: command to execute
        @type command: str or L{dtestlib.executor.dataobjects.command.Command}
        @return: list of result objects L{dtestlib.executor.networkobjects_tests.exec_result.ExecResult} with provided API
        @rtype: list
        """
        res_list = self.execute_everywhere(command)
        self.wait(res_list)
        return res_list

    def execute_batch_everywhere(self, commands=()):
        """
        Executes a set of commands on every available connection
        @param command: A set of commands to be executed
        @type command: iterable
        @return: list of lists of result objects L{dtestlib.executor.networkobjects_tests.exec_result.ExecResult} with provided API
        @rtype: list
        """
        res_list = []
        for connection in Connection:
            results = self.model.execute_batch(commands=commands, connection=connection)
            res_list.append(results)
        return res_list

    def execute_batch_everywhere_wait(self, commands=()):
        """
        Executes a set of commands on every available connection
        @param command: A set of commands to be executed
        @type command: iterable
        @return: list of lists of result objects L{dtestlib.executor.networkobjects_tests.exec_result.ExecResult} with provided API
        @rtype: list
        """
        res_list = self.execute_batch_everywhere(commands)
        self.wait(res_list)
        return res_list

    def wait(self, results=[]):
        # TODO naive approach
        if len(results) > 0 and hasattr(results[0], "__iter__"):
            for result_list in results:
                self.wait(result_list)
        else:
            for result in results:
                result.wait_for_data()

    def kill(self, command, sig=signal.SIGTERM):
        """
        This function is not required and will be deleted.
        """
        return self.model.kill(command=command, sig=sig)

    def create_connection(self, host, user):
        """
        Create connection and returns it.
        Created connection is added automatically to the the pool of connections.
        @param host: host object
        @type host: L{dtestlib.executor.networkobjects_tests.host.Host}
        @param user: user object of type
        @type user: L{dtestlib.executor.networkobjects_tests.user.User}
        @return: created connection
        @rtype: L{dtestlib.executor.networkobjects_tests.connection.Connection}
        """
        return self.model.create_connection(host=host, user=user)

    def connect(self, connection=None):
        """
        Connects via underlying module using specified connection object
        @param connection: connection object
        @type connection: L{dtestlib.executor.networkobjects_tests.connection.Connection}
        @return: None
        @rtype: None
        """
        self.model.connect(connection=connection)

    def get_connection(self, host=None, user=None):
        return self.model.get_connection(host=host, user=user)

    def close_connection(self, connection=None):
        return self.model.close_connection(connection=connection)
