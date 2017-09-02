import time

import pytest
from mock import Mock

from executor_exceptions import *
from models.paramiko_model import ParamikoModel
from networkobjects.command import Command
from networkobjects.connection import Connection
from networkobjects.exec_result import ExecResult
from networkobjects.host import Host
from networkobjects.user import User

connection = None
host = None
user = None
client = None
invalid_cmd = None
func_mock = None


@pytest.fixture
def model():
    return ParamikoModel()


@pytest.fixture(autouse=True)
def reset():
    global connection
    global user
    global host
    global client
    global invalid_cmd
    global func_mock
    func_mock = Mock()
    invalid_cmd = Command("invalid_cmd")
    connection = None
    user = User()
    host = Host()
    client = "empty"
    ParamikoModel.active_connection = None


def test_create_connection(monkeypatch, model):
    mock_client = Mock()
    monkeypatch.setattr(ParamikoModel, "__create_initialized_client__",
                        mock_client)  # to be able to create same connection
    model_conn = model.create_connection(host, user)
    connection = Connection(host=host, user=user, client=client)
    assert model_conn == connection


# here are not used "host" and "user" objects from reset, because during test_data construction they are both None
test_data = [(Host(), None, InvalidUserException), (None, User(), InvalidHostException)]


@pytest.mark.parametrize("host, user, exception", test_data, ids=["invalid_user_exception", "invalid_host_exception"])
def test_create_conection_raises(model, host, user, exception):
    with pytest.raises(exception):
        model.create_connection(host, user)


def test_connect_raises_invalid_connection(model):
    with pytest.raises(InvalidConnection):
        model.connect(None)


# here are not used "host" and "user" objects from reset, because during test_data construction they are both None
test_data = [(Host(), User(username="tester"), ConnectionNotFound),
             (Host(), None, InvalidUserException),
             (None, User(), InvalidHostException)]


@pytest.mark.parametrize("host, user, exception", test_data,
                         ids=["connection_not_found", "invalid_user_exception", "invalid_host_exception"])
def test_get_connection_raises(model, host, user, exception):
    with pytest.raises(exception):
        model.get_connection(host, user)


def test_get_connection(model):
    model_conn = model.create_connection(host, user)
    output_con = model.get_connection(host=host, user=user)
    assert output_con == model_conn


def test_close_connection(model):
    model_conn = model.create_connection(host, user)
    assert model_conn in host.connections
    assert model_conn in user.connections
    assert model_conn in Connection
    model.close_connection(model_conn)
    assert model_conn not in host.connections
    assert model_conn not in user.connections
    assert model_conn not in Connection


def test_close_connection_raises_close_error(model):
    with pytest.raises(ConnectionCloseError):
        model.close_connection()


test_data = [(None, Command("test_cmd"), "test_con", InvalidChannelException),
             ("test_channel", None, "test_con", InvalidCommandValue),
             ("test_channel", Command("test_cmd"), None, InvalidConnection)]


@pytest.mark.parametrize("channel, cmd, connection, exception",
                         test_data,
                         ids=["invalid_channel_exception", "invalid_command_value", "invalid_connection"])
def test_create_result_raises(model, channel, cmd, connection, exception):
    with pytest.raises(exception):
        model._create_result(channel=channel, command=cmd, connection=connection)


def test_create_result(monkeypatch, model):
    channel = "test_channel"
    monkeypatch.setattr(model, "__receive_stdout__",
                        func_mock)  # to be able to create same result
    monkeypatch.setattr(model, "__receive_stderr__",
                        func_mock)  # to be able to create same result
    conn = model.create_connection(user=user, host=host)

    model_res = model._create_result(channel=channel, command=invalid_cmd, connection=conn)
    test_res = ExecResult(command=invalid_cmd,
                          receive_stdout_func=func_mock,
                          receive_stderr_func=func_mock,
                          exit_status_func=func_mock,
                          connection=conn)
    assert model_res.cmd == test_res.cmd
    assert model_res.connection == test_res.connection


def test_kill_raises_invalid_command_value(model):
    with pytest.raises(InvalidCommandValue):
        model.kill(command=None)


def test_kill(monkeypatch, model):
    connection = model.create_connection(host=host, user=user)
    command_to_kill = model.create_command("test")
    command_to_kill.pid = 2555
    command_to_kill.connection = connection
    time_val = time.time()
    transport_mock = Mock(spec=["open_session"])
    time_mock = Mock(return_value=time_val)
    res_wait_mock = Mock(spec="wait_for_data")

    monkeypatch.setattr(connection.client, "get_transport", transport_mock)
    monkeypatch.setattr(time, "time", time_mock)
    monkeypatch.setattr(ExecResult, "wait_for_data", res_wait_mock)

    ecode = model.kill(command=command_to_kill)
    assert ecode == None
    assert len(connection.incomplete_results) == 1
    res = connection.incomplete_results.pop()
    model_kill_cmd = model.create_command("kill -15 2555")
    assert res.cmd.cmd == model_kill_cmd.cmd


def test_create_commad_raises_invalid_command_value(model):
    with pytest.raises(InvalidCommandValue):
        model.create_command(command=None)


def test_create_command(model):
    model_command = model.create_command(command=invalid_cmd.cmd)
    assert invalid_cmd.cmd == model_command.cmd


test_data = [(tuple("invalid_cmd"), None, InvalidConnection),
             (None, "invalid_con", InvalidCommandValue),
             ("invalid_cmd", "invalid_con", InvalidCommandValue)]


@pytest.mark.parametrize("command, connection, exception", test_data,
                         ids=["invalid_connection", "invalid_command_value_none", "invalid_command_value_iter"])
def test_execute_batch_raises(model, command, connection, exception):
    with pytest.raises(exception):
        model.execute_batch(commands=command, connection=connection)


test_data = [("invalid_cmd", None, InvalidConnection),
             (None, "invalid_con", InvalidCommandValue)]


@pytest.mark.parametrize("command, connection, exception", test_data,
                         ids=["invalid_connection", "invalid_command_value"])
def test_execute_raises(model, command, connection, exception):
    with pytest.raises(exception):
        model.execute(command=command, connection=connection)


test_data = [(tuple((Command("test_cmd1"), Command("test_cmd2")))), (tuple(("test_cmd1", "test_cmd2")))]


@pytest.mark.parametrize("cmds", test_data, ids=["object", "string"])
def test_execute_batch(monkeypatch, model, cmds):
    conn = model.create_connection(host=host, user=user)
    time_val = time.time()
    cmd_pool = []
    for cmd in cmds:
        if hasattr(cmd, "cmd"):
            cmd = cmd.cmd
        cmd_to_compare = model.create_command(cmd)
        cmd_to_compare.connection = conn
        cmd_to_compare.time_stamp = time_val
        cmd_pool.append(cmd_to_compare)
    transport_mock = Mock(spec=["open_session"])
    time_mock = Mock(return_value=time_val)

    monkeypatch.setattr(conn.client, "get_transport", transport_mock)
    monkeypatch.setattr(time, "time", time_mock)
    res_list = model.execute_batch(commands=cmds, connection=conn)

    assert len(conn.incomplete_results) == len(cmd_pool)
    assert len(cmd_pool) == len(res_list)
    for x in xrange(len(res_list)):
        model_res = res_list[x]
        cmd_to_compare = cmd_pool[x]
    assert model_res.cmd.cmd == cmd_to_compare.cmd
    assert model_res.cmd.time_stamp == cmd_to_compare.time_stamp
    assert model_res.cmd.connection == cmd_to_compare.connection
    assert model_res.connection == conn


test_data = [(Command("test_cmd")), ("test_cmd")]


@pytest.mark.parametrize("cmd", test_data, ids=["object", "string"])
def test_execute_cmd(monkeypatch, model, cmd):
    conn = model.create_connection(host=host, user=user)
    time_val = time.time()
    if hasattr(cmd, "cmd"):
        cmd = cmd.cmd
    cmd_to_compare = model.create_command(cmd)
    cmd_to_compare.connection = conn
    cmd_to_compare.time_stamp = time_val
    transport_mock = Mock(spec=["open_session"])
    time_mock = Mock(return_value=time_val)

    monkeypatch.setattr(conn.client, "get_transport", transport_mock)
    monkeypatch.setattr(time, "time", time_mock)
    model_res = model.execute(command=cmd, connection=conn)

    assert len(conn.incomplete_results) == 1
    assert model_res.cmd.cmd == cmd_to_compare.cmd
    assert model_res.cmd.time_stamp == cmd_to_compare.time_stamp
    assert model_res.cmd.connection == cmd_to_compare.connection
    assert model_res.connection == conn
