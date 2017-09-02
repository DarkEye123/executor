from . import logger

__author__ = 'mlesko'

import paramiko
from executor_exceptions import *
from paramiko import SSHClient
from networkobjects.exec_result import ExecResult
from networkobjects.host import Host
from networkobjects.user import User
from remote_execution_template import RemoteExecutionTemplate
from networkobjects.connection import Connection
from networkobjects.command import Command
import time
import signal


class ParamikoModel(RemoteExecutionTemplate):
    """
    ParamikoModel class uses paramiko module for remote execution.
    Provides API compatible with L{dtestlib.executor.executor.Executor} and maps its
    functionality to instances of classes from dtestlib.executor.networkobjects_tests

    @author mlesko
    """
    reconnect_ena = False
    auto_add_policy = True
    buffer_size = 10485760  # total number of bytes fetched from the stream  = 10 Mb --> per session
    active_connection = None

    @classmethod
    def _set_connection(cls, connection=None):  # TODO possible refactoring to property
        """
        Set connection to defined or active one
        There is no need to examine the value of connection parameter in the code directly
        @param connection: connection to be used
        @type connection: Connection
        @return: connection to be used
        @rtype: Connection
        """
        conn = connection or cls.active_connection
        if conn is None:
            raise InvalidConnection('Connection must be set before executing command')
        return conn

    @classmethod
    def __create_initialized_client__(cls):
        """
        Initialize instance of paramiko.SSHClient and fills necessary internal parameters.
        @return: initialized client
        @rtype: paramiko.SSHClient
        """
        client = SSHClient()
        if cls.auto_add_policy:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client

    def create_connection(self, host, user):
        """
        Create connection. If connection already exists the creation is skipped.
        @param host: host to connect to
        @type host: Host
        @param user: user to be used during connection
        @type user: User
        @return: connection object
        @rtype: Connection
        """
        connection = Connection.find(host, user)
        if connection is None:  # it means this is new connection and not from the pool, so no functionality is mapped
            client = ParamikoModel.__create_initialized_client__()
            # execute, execute batch and close methods need to be mapped after object creation
            connection = super(ParamikoModel, self).create_connection(host=host, user=user, client=client)
            connection._execute_fn = lambda cmd: self.execute(command=cmd, connection=connection)
            connection._execute_batch_fn = lambda cmd: self.execute_batch(commands=cmd, connection=connection)
            connection._close_f = lambda: self.close_connection(connection=connection)
            connection._connect = lambda: self.connect(connection=connection)
            logger.debug(str(connection) + " functionality mapping done")
        ParamikoModel.active_connection = connection
        return connection

    def connect(self, connection=None):
        """
        Connects via underlying module using specified connection object.
        If connection object was already connected connecting is skipped.
        @param connection: connection object to be used
        @type connection: Connection
        @raise InvalidConnection: if connection is not instance of L{dtestlib.executor.networkobjects_tests.connection.Connection} class
        @return: None
        @rtype: None
        """

        _connection = self._set_connection(connection)
        if not isinstance(_connection, Connection):
            raise InvalidConnection("connection must be an instance of the Connection class")

        if not _connection.connected:
            logger.debug(str(_connection) + " is connecting.")
            _connection.client.connect(hostname=_connection.host.address, port=_connection.host.port,
                                       username=_connection.user.username, password=_connection.user.password)

    def get_connection(self, host=None, user=None):
        """
        Return connection assigned to host and user combination. If such connection does not exist
        a none is returned.
        @param host: host to connect to
        @type host: Host
        @param user: user to be used for authorization
        @type user: User
        @return: connection or none
        @rtype: Connection
        """
        connection = super(ParamikoModel, self).get_connection(host, user)
        # TODO reconsider what this is good for, or add counter of reconnects
        if connection.client.get_transport() is not None:
            if not connection.client.get_transport().is_authenticated() and self.reconnect_ena:
                self.connect(connection)
        ParamikoModel.active_connection = connection
        return connection

    def close_connection(self, connection=None):
        """
        Closes connection - invalidates it for further usage
        In case an connection is not provided the active connection will be closed
        @param connection: connection to be closed
        @type connection: Connection
        @raise ConnectionCloseError: if connection could not be closed, caused by invalid connection
        @return: None
        @rtype: None
        """
        tmp_conn = ParamikoModel.active_connection
        try:
            _connection = self._set_connection(connection)
        except InvalidConnection:
            raise ConnectionCloseError("connection must be an instance of the Connection class")
        if ParamikoModel.active_connection == tmp_conn:  # active connection was deleted
            ParamikoModel.active_connection = None
            logger.debug("close_connection set active_connection to None")
        else:
            ParamikoModel.active_connection = tmp_conn
        _connection.client.close()
        logger.debug("Removing connection %s from %s" % (_connection, _connection.host))
        _connection.host.connections.remove(_connection)
        logger.debug("Connections left in host: %s" % _connection.host.connections)
        logger.debug("Removing connection %s from %s" % (_connection, _connection.user))
        _connection.user.connections.remove(_connection)
        logger.debug("Connections left in user: %s" % _connection.user.connections)
        _connection._close()  # there can be independent tear_down functionality from the model

    def _create_result(self, channel=None, command=None, connection=None):
        """
        Create result object which stores its command and connection where it was executed.
        @param channel: `Channels <.Channel>` are
            socket-like objects used for the actual transfer of data across the
            session.
        @type channel: paramiko.channel.Channel
        @param command: command associated with the result, it may be string or Command instance
        @type command: Command
        @param connection: connection on which is the result available and is associated with
        @type connection: Connection
        @return: object representing a result of the command execution with associated data
        @rtype: ExecResult
        """
        if channel is None:
            raise InvalidChannelException("channel need to be specified during result obtaining")
        if not isinstance(command, Command):
            raise InvalidCommandValue("command must be an instance of the Command class")
        if not isinstance(connection, Connection):
            raise InvalidConnection("connection can't be None")
        result = ExecResult(
            command=command,
            receive_stdout_func=lambda output_data: self.__receive_stdout__(channel, output_data),
            receive_stderr_func=lambda output_data: self.__receive_stderr__(channel, output_data),
            exit_status_func=lambda: channel.recv_exit_status(),
            connection=connection
        )
        return result

    def kill(self, command, sig=signal.SIGTERM):  # TODO possible removal, unnecessary, wrapper do this
        """
        Executes kill on given command with signal
        @param command: command to be killed
        @type command: L{dtestlib.executor.networkobjects_tests.command.Command}
        @param sig: signal to send to the running process, see L{signal.py}
        @type sig: int
        @return: ecode of kill command
        @rtype: int
        """
        if not isinstance(command, Command):
            raise InvalidCommandValue("cmd must be an instance of the Command class")

        command = Command('kill -%s %s' % (sig, command.pid))
        tmp_con = ParamikoModel.active_connection
        res = self.execute(command=command, connection=command.connection)
        res.wait_for_data()
        ParamikoModel.active_connection = tmp_con  # restore previous active connection
        return res.ecode

    def create_command(self, command):
        """
        Create an instance of L{Command} class.
        @param command: command to be executed
        @type command: Command
        @return: command
        @rtype: Command
        """
        if not isinstance(command, basestring):
            raise InvalidCommandValue("cmd must be instance of the string")
        command = Command(command=command)
        command._kill_func = lambda sig: self.kill(command=command, sig=sig)
        return command

    def __receive_stdout__(self, channel, output_data):
        """
        Provides a function to read from the channel a stream of bytes from standard output stream
        @param channel: `Channels <.Channel>` are
            socket-like objects used for the actual transfer of data across the
            session.
        @type channel: paramiko.channel.Channel
        @param output_data: list where an output will be stored
        @type output_data: list
        @return: function for stdout manipulation
        @rtype: object reference
        """
        return self.__read_from_stream__(lambda: channel.recv(self.buffer_size), output_data)

    def __receive_stderr__(self, channel, output_data):
        """
        Provides a function to read from the channel a stream of bytes from standard error stream
        @param channel: `Channels <.Channel>` are
            socket-like objects used for the actual transfer of data across the
            session.
        @type channel: paramiko.channel.Channel
        @param output_data: list where an output will be stored
        @type output_data: list
        @return: function for stderr manipulation
        @rtype: object reference
        """
        return self.__read_from_stream__(lambda: channel.recv_stderr(self.buffer_size),
                                         output_data)

    def __read_from_stream__(self, stream_manipulation_func, output_data):
        """
        Universal approach how to use same functionality for different stream manipulation methods
        @param channel: `Channels <.Channel>` are
            socket-like objects used for the actual transfer of data across the
            session.
        @type channel: paramiko.channel.Channel
        @param ask_status_func: function used for checking the transfer status
        @param stream_manipulation_func:  function provides transfer of the data
        @param output_data: storage of the output data
        @type output_data: list
        @return: wrapped function
        @rtype: object reference
        """
        WAIT_FOR_DATA = 0.01  # in tests this was with best results

        def wrapper():
            output_data.append('')
            while True:
                received = stream_manipulation_func()  # this has to be stream of bytes
                if received == '':  # faster than len(string) == 0 comparing
                    break
                output_data[0] = "%s%s" % (output_data[0], received)
                time.sleep(WAIT_FOR_DATA)
            return output_data[0].splitlines()

        return wrapper

    def execute_batch(self, commands=(), connection=None):
        """
        Execute a batch of commands in a simultaneous way.
        @param commands: list of commands. Command can be string or an instance of the class L{Command}
        @type commands: list | tuple
        @param connection: connection object on which a batch will be executed
        @type connection: Connection
        @return: list of results of the type L{ExecResult}
        @rtype: list
        @raise InvalidCommandValue: if commands are not iterable or the content of the list is not executable
        """
        if commands is None:
            raise InvalidCommandValue("Command can't be None")
        if not hasattr(commands, "__iter__"):
            raise InvalidCommandValue("Command needs to be an iterable")
        result_list = []
        for cmd in commands:
            res = self.execute(command=cmd, connection=connection)
            result_list.append(res)
            if res.cmd.exclusive:
                res.wait_for_data()
        return result_list

    def execute(self, command=None, connection=None):
        """
        Execute command on the connection
        @param command: command to be executed
        @type command: str | Command
        @param connection: connection on which the command will be executed
        @type connection: Connection
        @return: result of the execution.
        @rtype: ExecResult
        @raise InvalidCommandValue: if command is not the L{Command} instance or an instance of the string
        """
        if not (isinstance(command, basestring) or isinstance(command, Command)):
            raise InvalidCommandValue("command must be the string or an instance of the Command class")
        conn = self._set_connection(connection)
        ssh_chnl = conn.client.get_transport().open_session()
        if not isinstance(command, Command):
            command = self.create_command(command)
        command.time_stamp = time.time()
        command.connection = conn
        logger.debug("[%s]$ %s" % (conn.id, command.cmd))
        ssh_chnl.exec_command(command.cmd)  # channel exec, not conn exec (see channel.py in paramiko)
        exec_result = self._create_result(channel=ssh_chnl, command=command, connection=conn)
        conn.incomplete_results.append(exec_result)
        return exec_result
