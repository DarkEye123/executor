from __future__ import absolute_import
import signal

import executor_exceptions

__author__ = 'mlesko'


# Create only via model for full functionality
class Command(object):
    """
    Class that represents a command as an object. Please be sure you are
    creating command via provided API of L{dtestlib.executor.executor.Executor}
    """

    def __init__(self, command=None, kill_func=None, exclusive=False):
        """
        Initialize command
        @param command: command to be executed
        @type command: str
        @param kill_func: function that is mapped to "kill" the command
        @param exclusive: Flag that marks exclusive execution. It means no other commands no matter what will be processed  before this command is processed
        @type exclusive: bool
        """

        if not isinstance(command, basestring):
            raise executor_exceptions.InvalidCommandValue("Command must be string")

        self.cmd = command
        self.stdin = None  # TODO ask about this zkraus
        self.time_stamp = None  # time should be filled right before execution #float (time.time())
        self.connection = None  # filled during execution
        self.pid = None  # filled during execution
        self._kill_func = kill_func  # kill is not mandatory during initialization due to possible problematic references in model. Please be sure what you are doing if you do not create Command via model method.
        self.exclusive = exclusive  # is this command exclusive - blocking - command? - such command blocks processing of another ones in the queue

    def kill(self, sig=signal.SIGTERM):
        """
        Kills executed command
        @param sig: signal to send to the executed command, see L{signal.py}
        @type sig: int
        @return: ecode of kill command
        @rtype: int
        @raise exceptions.MissingFunctionDefinition: when command is created outside of provided API and not properly provided with kill functionality
        """
        if self._kill_func is None:  # this is not done during initialization
            raise executor_exceptions.MissingFunctionDefinition("Kill function was not mapped")
        return self._kill_func(sig)
