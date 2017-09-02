import time

import pytest
from mock import Mock

from executor_exceptions import *
from models.paramiko_model import ParamikoModel
from networkobjects.command import Command
from networkobjects.exec_result import ExecResult
from networkobjects.host import Host
from networkobjects.user import User

model = ParamikoModel()


@pytest.fixture()
def exec_result():
    conn = model.create_connection(Host(), User())
    return ExecResult(Command("test"), Mock(), Mock(), Mock(), conn)


test_data = [
    (None, None, None, None, None, InvalidCommandValue),
    (Command("cmd"), None, None, None, None, MissingFunctionDefinition),
    (Command("cmd"), "invalid_f", None, None, None, MissingFunctionDefinition),
    (Command("cmd"), "invalid_f", "invalid_f", None, None, MissingFunctionDefinition),
    (Command("cmd"), "invalid_f", "invalid_f", "invalid_f", None, InvalidConnection)
]


@pytest.mark.parametrize(
    "command, exit_status_func, receive_stdout_func, receive_stderr_func, connection, exception", test_data,
    ids=["invalid_command_value", "missing_func_def_exit_status_func", "missing_func_def_receive_stdout_func",
         "missing_func_def_receive_stderr_func", "invalid_connection"])
def test_exec_result_init_raises(command, exit_status_func, receive_stdout_func, receive_stderr_func,
                                 connection, exception):
    with pytest.raises(exception):
        ExecResult(command, exit_status_func, receive_stdout_func, receive_stderr_func, connection)


def test_cmd_interconnect(exec_result):
    assert exec_result.cmd.result == exec_result


test_data = [(None, None, None), (10, None, None), (6, 10, 4)]


@pytest.mark.parametrize("ts_start, ts_stop, expected_result", test_data,
                         ids=["none_ts_start", "none_ts_stop", "valid_diff"])
def test_time_property_returns(monkeypatch, exec_result, ts_start, ts_stop, expected_result):
    monkeypatch.setattr(exec_result, "ts_start", ts_start)
    monkeypatch.setattr(exec_result, "ts_stop", ts_stop)
    assert exec_result.time == expected_result


@pytest.mark.timeout(5)
def test_wait_for_data(monkeypatch):
    stop_t = time.time()
    # exec result calls these functions with its own arguments, that is why is there lambda
    mock_stdout = Mock(return_value=lambda: "std_out")
    mock_stderr = Mock(return_value=lambda: "std_err")
    mock_exit_func = Mock(return_value="0")
    mock_time = Mock(return_value=stop_t)
    monkeypatch.setattr(time, "time", mock_time)
    conn = model.create_connection(Host(), User())
    result = ExecResult(Command("test"), mock_exit_func, mock_stdout, mock_stderr, conn)
    result.wait_for_data()
    assert result.ts_stop == stop_t
    assert result._stdout == mock_stdout()()
    assert result._stderr == mock_stderr()()
    assert result.ecode == mock_exit_func()
