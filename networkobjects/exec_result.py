import time
from multiprocessing.pool import ThreadPool

from command import Command
from connection import Connection
import executor_exceptions
from . import logger

__author__ = 'mlesko'


class ExecResult(object):
    """
    Represents a result of the execution of the command. All functionality is mapped
    by the model.
    """

    # TODO process_id, user_name(credentials), sys_prof (test_node object teoreticky),
    def __init__(self, command=None, exit_status_func=None, receive_stdout_func=None, receive_stderr_func=None,
                 connection=None):
        """
        @param command: command that was executed and is associated with its result
        @type command: Command
        @param exit_status_func: function that is used for checking the exit status
        @param receive_stdout_func: function used for stdout receiving
        @param receive_stderr_func: function used for stderr receiving
        @param connection: connection object associated with the executed command and result
        @type connection: Connection
        """
        if not isinstance(command, Command):
            raise executor_exceptions.InvalidCommandValue("cmd must be an instance of the Command class")
        if receive_stdout_func is None or receive_stderr_func is None or exit_status_func is None:
            raise executor_exceptions.MissingFunctionDefinition
        if not isinstance(connection, Connection):
            raise executor_exceptions.InvalidConnection("connection must be an instance of Connection class")

        self.connection = connection
        self._stdout = []
        self._stderr = []
        self.ecode = None
        self.ts_start = command.time_stamp  # float (time.time())
        self.stdin = command.stdin
        self.ts_stop = None
        self._exit_status_f = exit_status_func
        self.result_available = False
        self.cmd = self.__cmd_interconnect__(command)  # position dependent initialization!!
        self.__fetch_streams(receive_stdout_func, receive_stderr_func)

    @property
    def stdout(self):
        if self.result_available:
            return self._stdout
        else:
            try:
                return self._stdout[0].splitlines()
            except IndexError:
                return self._stdout

    @stdout.setter
    def stdout(self, value):
        self._stdout = value

    @property
    def stderr(self):
        if self.result_available:
            return self._stderr
        else:
            try:
                return self._stderr[0].splitlines()
            except IndexError:
                return self._stderr

    @stderr.setter
    def stderr(self, value):
        self._stderr = value

    def __cmd_interconnect__(self, cmd):
        """
        Assign result instance to command instance.
        @param cmd: a command which is associated with the result instance
        @type cmd: Command
        @return: command which has assigned result instance
        @rtype: Command
        """
        cmd.result = self
        return cmd

    @property
    def time(self):
        """
        Property which represents time which the command execution took
        @return: time in seconds
        @rtype: int
        """
        if self.ts_start is not None and self.ts_stop is not None:
            return self.ts_stop - self.ts_start
        return None

    def wait_for_data(self):  # API for user to actually wait on the place
        """
        Waits till all data from the execution of the associated command
        are available. In the reality data are always fetched on the background.
        This method provide a way how to specify a waiting.
        @rtype: None
        """
        # WAIT_FOR_DATA = 0.1
        logger.debug("RESULT wait_for_data available %s -> command: %s" % (self.result_available, self.cmd.cmd))
        if not self.result_available:
            # this is multithreading.pool.ApplyResult instance
            self.__wait_thread.wait()  # waits till are data provided via mapped function

    def _wait_for_data(self):  # automatically fetches data -- this is necessary for background client method
        """
        After an execution, data are automatically fetched on the background by a
        special thread. This method uses a time pooling. This decision was made
        due to numerous facts:

          1. Data needs to be accessible before the commands execution ends.
          2. Wait based on events (no time pooling) causes data stuck if there is
             bigger output.
          3. There is a need to fetch stderr & stdout simultaneously therefore
             a threaded approach is used. For this purpose a multiprocessing module
             is used which offers real threads. It enables Python to utilize
             multiple CPU cores in parallel by running additional interpreters
             as child processes. These child processes are separate from the
             main interpreter, so their global interpreter locks are also separate.
             Each child can fully utilize one CPU core. Each child has a link to
             the main process where it receives instructions to do computation and returns
             results. This basically provides independent data fetching.
          3. Commands on this underlying layer are small and fast to execute.

        @warning: This method is not for direct call.
        @rtype: None
        """
        WAIT_FOR_DATA = 0.01

        # logger.debug("RESULT wait  available %s -> command: %s" % (self.result_available, self.cmd.cmd))
        if not self.result_available:

            # another approach causes the famous "stuck" during big inputs
            while not (self.__stdout_async_r.ready() and self.__stderr_async_r.ready()):
                # logger.debug("WAITING threads for command: %s" % self.cmd.cmd)
                time.sleep(WAIT_FOR_DATA)

            self.result_available = True
            self.ts_stop = time.time()  # float
            # these are multithreading.pool.ApplyResult instances
            self._stdout = self.__stdout_async_r.get()
            self._stderr = self.__stderr_async_r.get()
            self.ecode = self._exit_status_f()  # this can be a waiting operation, therefore status is received at the last place
            logger.debug("Closing threads for command: %s" % self.cmd.cmd)
            self.stdout_t.close()
            logger.debug("Closed stdout thread")
            self.stderr_t.close()
            logger.debug("Closed stderr thread")
            self.wait_thread.close()
            logger.debug("Closed wait thread")
            logger.debug("Joining threads for command: %s" % self.cmd.cmd)
            self.stdout_t.join()
            logger.debug("Joined stdout thread")
            self.stderr_t.join()
            logger.debug("Joined stderr thread")
            # self.wait_thread.join()
            # logger.debug("Joined wait thread")
            logger.debug("Threads joined for command: %s" % self.cmd.cmd)

    # This could be done better (more generic), but it would be not beneficial because no other unknown streams will be read
    def __fetch_streams(self, stdout_func, stderr_func):
        """
        Fetches streams using threaded approach to prevent a stuck during big inputs.
        This problem appears in paramiko package. But it is normal behavior of network
        channel. Therefore, an universal approach was needed.
        @param stdout_func: function for stdout receiving provided by model
        @param stderr_func: function for stderr receiving provided by model
        @warning: This method is not for direct call.
        @rtype: None
        """
        stdout_t = ThreadPool(processes=1)
        stderr_t = ThreadPool(processes=1)
        wait_thread = ThreadPool(processes=1)

        self.stdout_t = stdout_t
        self.stderr_t = stderr_t
        self.wait_thread = wait_thread

        # method apply_async creates multithreading.pool.ApplyResult instances
        self.__stdout_async_r = stdout_t.apply_async(func=stdout_func(self._stdout))
        self.__stderr_async_r = stderr_t.apply_async(func=stderr_func(self._stderr))
        self.__wait_thread = wait_thread.apply_async(
            func=self._wait_for_data)  # THIS IS EXTREMELY NECESSARY for start_background
