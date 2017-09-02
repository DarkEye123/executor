import pytest

from executor_exceptions import InvalidCommandValue, MissingFunctionDefinition
from networkobjects.command import Command


def test_command_init_raises_invalid_command_value():
    with pytest.raises(InvalidCommandValue):
        Command(command=None)


def test_kill_raises_missing_function_definition():
    with pytest.raises(MissingFunctionDefinition):
        cmd = Command(command="cmd")
        cmd.kill()
