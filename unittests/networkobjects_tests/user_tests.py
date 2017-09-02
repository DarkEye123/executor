import pytest

from executor_exceptions import *
from networkobjects.user import User


def test_user_create_raises_invalid_username_exception():
    with pytest.raises(InvalidUsernameExeption):
        User(username=None)


def test_user_create_only_once():
    conn1 = "false_conn1"
    conn2 = "false_conn2"
    user = User()
    user.connections.add(conn1)
    user.connections.add(conn2)
    user = User()  # returns previously created user object
    assert len(user.connections)
    assert user.connections.pop() == conn1
    assert user.connections.pop() == conn2


def test_user_generate_id_public_raises_invalid_username_exception():
    with pytest.raises(InvalidUsernameExeption):
        User.generate_id(username=None, password=None)


def test_user_generate_id_public():
    username = "user"
    password = "pass"
    sim_id = "%s:%s" % (username, password)
    user = User(username=username, password=password)
    gen_id = User.generate_id(username=username, password=password)
    assert user.id == gen_id
    assert gen_id == sim_id


def test_user_generate_id_protected():
    username = "user"
    password = "pass"
    sim_id = "%s:%s" % (username, password)
    user = User(username=username, password=password)
    gen_id = User._generate_id(username=username, password=password)
    assert user.id == gen_id
    assert gen_id == sim_id
