from __future__ import absolute_import

import time

import pytest
from mock import Mock

from models.paramiko_model import ParamikoModel
from networkobjects.command import Command
from networkobjects.connection import Connection
from networkobjects.exec_result import ExecResult
from networkobjects.host import Host
from networkobjects.user import User
from ..executor import Executor
from executor_exceptions import *


@pytest.fixture()
def executor():
    return Executor()


@pytest.fixture(autouse=True)
def reset():
    ParamikoModel.active_connection = None


def test_executor_init_raises_invalid_model_exception():
    with pytest.raises(InvalidModelException):
        Executor(model=None)


def test_iter_connections(executor):
    conn_pool = []
    for x in xrange(3):
        host = Host(address=str(x))
        conn_pool.append(executor.create_connection(host, User()))

    for conn in executor.iter_connections():
        assert conn in Connection
        assert conn in conn_pool
        conn_pool.remove(conn)

    assert len(list(executor.iter_connections())) == len(Connection)
    assert len(conn_pool) == 0


def test_iter_hosts(executor):
    host_pool = []
    for x in xrange(3):
        host = Host(address=str(x))
        host_pool.append(host)

    for host in executor.iter_hosts():
        assert host in Host
        assert host in host_pool
        host_pool.remove(host)

    assert len(list(executor.iter_hosts())) == len(Host)
    assert len(host_pool) == 0


def test_iter_users(executor):
    user_pool = []
    for x in xrange(3):
        user = User(password=str(x))
        user_pool.append(user)

    for user in executor.iter_users():
        assert user in User
        assert user in user_pool
        user_pool.remove(user)

    assert len(list(executor.iter_users())) == len(User)
    assert len(user_pool) == 0


def test_create_command_raises_invalid_command_value(executor):
    with pytest.raises(InvalidCommandValue):
        executor.create_command(command=None)


def test_create_command(executor):
    cmd_text = "test"
    cmd = executor.create_command(cmd_text)
    assert cmd.cmd == cmd_text
    assert cmd._kill_func != None


test_data = [(tuple("invalid_cmd"), None, InvalidConnection),
             (None, "invalid_con", InvalidCommandValue),
             ("invalid_cmd", "invalid_con", InvalidCommandValue)]


@pytest.mark.parametrize("command, connection, exception", test_data,
                         ids=["invalid_connection", "invalid_command_value_none", "invalid_command_value_iter"])
def test_execute_batch_raises(executor, command, connection, exception):
    with pytest.raises(exception):
        executor.execute_batch(commands=command, connection=connection)


test_data = [(tuple((Command("test_cmd1"), Command("test_cmd2")))), (tuple(("test_cmd1", "test_cmd2")))]


@pytest.mark.parametrize("cmds", test_data, ids=["object", "string"])
def test_execute_batch(monkeypatch, executor, cmds):
    conn = executor.create_connection(host=Host(), user=User())
    time_val = time.time()
    cmd_pool = []
    for cmd in cmds:
        if hasattr(cmd, "cmd"):
            cmd = cmd.cmd
        cmd_to_compare = executor.create_command(cmd)
        cmd_to_compare.connection = conn
        cmd_to_compare.time_stamp = time_val
        cmd_pool.append(cmd_to_compare)
    client_mock = Mock()
    time_mock = Mock(return_value=time_val)

    monkeypatch.setattr(conn, "client", client_mock)
    monkeypatch.setattr(time, "time", time_mock)
    res_list = executor.execute_batch(commands=cmds, connection=conn)

    assert len(conn.incomplete_results) == len(cmd_pool)
    assert len(cmd_pool) == len(res_list)
    for x in xrange(len(res_list)):
        model_res = res_list[x]
        cmd_to_compare = cmd_pool[x]
    assert model_res.cmd.cmd == cmd_to_compare.cmd
    assert model_res.cmd.time_stamp == cmd_to_compare.time_stamp
    assert model_res.cmd.connection == cmd_to_compare.connection
    assert model_res.connection == conn


test_data = [("invalid_cmd", None, InvalidConnection),
             (None, "invalid_con", InvalidCommandValue)]


@pytest.mark.parametrize("command, connection, exception", test_data,
                         ids=["invalid_connection", "invalid_command_value"])
def test_execute_raises(executor, command, connection, exception):
    with pytest.raises(exception):
        executor.execute(command=command, connection=connection)


test_data = [(Command("test_cmd")), ("test_cmd")]


@pytest.mark.parametrize("cmd", test_data, ids=["object", "string"])
def test_execute_cmd(monkeypatch, executor, cmd):
    conn = executor.create_connection(host=Host(), user=User())
    time_val = time.time()
    if hasattr(cmd, "cmd"):
        cmd = cmd.cmd
    cmd_to_compare = executor.create_command(cmd)
    cmd_to_compare.connection = conn
    cmd_to_compare.time_stamp = time_val
    client_mock = Mock()
    time_mock = Mock(return_value=time_val)

    monkeypatch.setattr(conn, "client", client_mock)
    monkeypatch.setattr(time, "time", time_mock)
    model_res = executor.execute(command=cmd, connection=conn)

    assert len(conn.incomplete_results) == 1
    assert model_res.cmd.cmd == cmd_to_compare.cmd
    assert model_res.cmd.time_stamp == cmd_to_compare.time_stamp
    assert model_res.cmd.connection == cmd_to_compare.connection
    assert model_res.connection == conn


def test_kill_raises_invalid_command_value(executor):
    with pytest.raises(InvalidCommandValue):
        executor.kill(command=None)


def test_kill(monkeypatch, executor):
    connection = executor.create_connection(host=Host(), user=User())
    command_to_kill = executor.create_command("test")
    command_to_kill.pid = 2555
    command_to_kill.connection = connection
    time_val = time.time()
    client_mock = Mock()
    time_mock = Mock(return_value=time_val)
    res_wait_mock = Mock(spec="wait_for_data")

    monkeypatch.setattr(connection, "client", client_mock)
    monkeypatch.setattr(time, "time", time_mock)
    monkeypatch.setattr(ExecResult, "wait_for_data", res_wait_mock)

    ecode = executor.kill(command=command_to_kill)
    assert ecode == None
    assert len(connection.incomplete_results) == 1
    res = connection.incomplete_results.pop()
    model_kill_cmd = executor.create_command("kill -15 2555")
    assert res.cmd.cmd == model_kill_cmd.cmd


def test_create_connection(monkeypatch, executor):
    client_mock = Mock()
    model_conn = executor.create_connection(host=Host(), user=User())
    monkeypatch.setattr(model_conn, "client", client_mock)
    connection = Connection(host=Host(), user=User(), client=client_mock())
    assert model_conn == connection


# here are not used "host" and "user" objects from reset, because during test_data construction they are both None
test_data = [(Host(), None, InvalidUserException), (None, User(), InvalidHostException)]


@pytest.mark.parametrize("host, user, exception", test_data, ids=["invalid_user_exception", "invalid_host_exception"])
def test_create_conection_raises(executor, host, user, exception):
    with pytest.raises(exception):
        executor.create_connection(host, user)


def test_connect_raises_invalid_connection(executor):
    with pytest.raises(InvalidConnection):
        executor.connect(None)


test_data = [(Host(), User(username="tester"), ConnectionNotFound),
             (Host(), None, InvalidUserException),
             (None, User(), InvalidHostException)]


@pytest.mark.parametrize("host, user, exception", test_data,
                         ids=["connection_not_found", "invalid_user_exception", "invalid_host_exception"])
def test_get_connection_raises(executor, host, user, exception):
    with pytest.raises(exception):
        executor.get_connection(host, user)


def test_get_connection(executor):
    model_conn = executor.create_connection(host=Host(), user=User())
    output_con = executor.get_connection(host=Host(), user=User())
    assert output_con == model_conn


def test_set_active_connection(executor):
    output_con = "test"
    executor.active_connection = "test"  # test of the underlying @property setter
    assert output_con == executor.active_connection


def test_close_connection(executor):
    host = Host()
    user = User()
    model_conn = executor.create_connection(host, user)
    assert model_conn in host.connections
    assert model_conn in user.connections
    assert model_conn in Connection
    executor.close_connection(model_conn)
    assert model_conn not in host.connections
    assert model_conn not in user.connections
    assert model_conn not in Connection


def test_close_connection_raises_close_error(executor):
    with pytest.raises(ConnectionCloseError):
        executor.close_connection()
