from __future__ import absolute_import

import pytest
from mock.mock import Mock

from networkobjects.command import Command
from networkobjects.connection import Connection
from networkobjects.host import Host
from networkobjects.user import User
from executor_exceptions import *

test_data = [(None, None, None, InvalidHostException),
             (Host(), None, None, InvalidUserException),
             (Host(), User(), None, InvalidClientException)]


@pytest.mark.parametrize("host, user, client, exception", test_data,
                         ids=["invalid_host_exception", "invalid_user_exception", "invalid_client_exception"])
def test_connection_create_raises(host, user, client, exception):
    with pytest.raises(exception):
        Connection(host, user, client)


def test_connection_create_only_once():
    test_client1 = "test_client1"
    test_client2 = "test_client2"
    conn1 = Connection(host=Host(), user=User(), client=test_client1)
    # this will return conn1, client may be changed at runtime
    conn2 = Connection(host=Host(), user=User(), client=test_client2)
    assert id(conn1) == id(conn2)


test_data = [(None, None, InvalidHostException),
             (Host(), None, InvalidUserException)]


@pytest.mark.parametrize("host, user, exception", test_data,
                         ids=["invalid_host_exception", "invalid_user_exception"])
def test_connection_generate_id_public_raises(host, user, exception):
    with pytest.raises(exception):
        Connection.generate_id(user=user, host=host)


def test_connection_generate_id_public():
    host = Host()
    user = User()
    sim_id = "%s@%s:%s" % (user.username, host.address, host.port)
    connection = Connection(host=host, user=user, client="empty")
    gen_id = Connection.generate_id(user=user, host=host)
    assert connection.id == gen_id
    assert gen_id == sim_id


def test_connection_generate_id_protected():
    host = Host()
    user = User()
    sim_id = "%s@%s:%s" % (user.username, host.address, host.port)
    connection = Connection(host=host, user=user, client="empty")
    gen_id = Connection._generate_id(user=user, host=host)
    assert connection.id == gen_id
    assert gen_id == sim_id


test_data = [(None, False), ("invalid_con", False),
             (Connection(Host(address="different"), User(), "empty"), False),
             (Connection(Host(), User(username="tester"), "empty"), False),
             (Connection(Host(), User(), "empty"), True)]


@pytest.mark.parametrize("other, expected_result", test_data,
                         ids=["invalid_obj_none", "invalid_obj_str", "different_id_user", "different_id_host",
                              "identical"])
def test_connection_eq(other, expected_result):
    conn = Connection(Host(), User(), "empty")
    cmp_res = conn == other
    assert cmp_res == expected_result


test_data = [(None, None, InvalidHostException),
             (Host(), None, InvalidUserException)]


@pytest.mark.parametrize("host, user, exception", test_data,
                         ids=["invalid_host_exception", "invalid_user_exception"])
def test_connection_find_raises(host, user, exception):
    with pytest.raises(exception):
        Connection.find(host, user)


test_data = [(Host(), User(username="tester"), False),
             (Host(address="addr"), User(), False),
             (Host(), User(), True)]


@pytest.mark.parametrize("host, user, expected_result", test_data,
                         ids=["none_by_user", "none_by_host", "identical"])
def test_connection_find(host, user, expected_result):
    connection = Connection(Host(), User(), "empty")
    find_conn = Connection.find(host, user)
    cmp_res = id(connection) == id(find_conn)
    assert cmp_res == expected_result


def test_connection_close_raises_missing_function_definition():
    with pytest.raises(MissingDefinitionException):
        conn = Connection(Host(), User(), "empty")
        conn.close()


def test_connection_connect_raises_missing_function_definition():
    with pytest.raises(MissingDefinitionException):
        conn = Connection(Host(), User(), "empty")
        conn.connect()


def test_connection_close(monkeypatch):
    conn = Connection(Host(), User(), "empty")
    monkeypatch.setattr(conn, "_close_f", conn._close)
    assert len(Connection.__pool__) == 1
    assert Connection.__pool__.get(conn.id) == conn
    conn.close()
    assert len(Connection.__pool__) == 0


def test_connection_get_available_results(monkeypatch):
    mock_available = Mock()
    mock_available.result_available = True
    mock_unavailable = Mock()
    mock_unavailable.result_available = False
    incomplete_list = [mock_available, mock_unavailable]
    expected_val_list = [mock_available]

    connection = Connection(Host(), User(), "empty")
    monkeypatch.setattr(connection, 'incomplete_results', incomplete_list)

    ret_list = connection.get_available_results()

    assert len(connection.incomplete_results) == 1
    assert connection.incomplete_results.pop() == mock_unavailable
    assert len(ret_list) == 1
    assert ret_list == expected_val_list


def test_connection_get_available_results_not_changing_original(monkeypatch):
    mock_available = Mock()
    mock_available.result_available = True
    mock_unavailable = Mock()
    mock_unavailable.result_available = False
    incomplete_list = [mock_available, mock_unavailable]

    connection = Connection(Host(), User(), "empty")
    monkeypatch.setattr(connection, 'incomplete_results', incomplete_list)

    tmp_ret_list = connection.get_available_results()
    tmp_ret_list.append(mock_unavailable)
    ret_list = connection.get_available_results()
    assert len(ret_list) == 1
    assert ret_list.pop() == mock_available


test_data = [(None, InvalidCommandValue), (Command("test"), MissingFunctionDefinition)]


@pytest.mark.parametrize("command, exception", test_data,
                         ids=["invalid_command_value", "missing_function_definition"])
def test_connection_execute_raises(command, exception):
    conn = Connection(Host(), User(), "empty")
    with pytest.raises(exception):
        conn.execute(command)


test_data = [("invalid_cmd", InvalidCommandValue),
             (tuple([Command("test")]), MissingFunctionDefinition)]


@pytest.mark.parametrize("command, exception", test_data,
                         ids=["invalid_command_value", "missing_function_definition"])
def test_connection_execute_batch_raises(command, exception):
    conn = Connection(Host(), User(), "empty")
    with pytest.raises(exception):
        conn.execute_batch(command)
