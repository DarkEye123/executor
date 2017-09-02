import pytest

from executor_exceptions import *
from models.remote_execution_template import RemoteExecutionTemplate
from networkobjects.host import Host
from networkobjects.user import User


# RemoteExecutionTemplate should be abstract
class TestClass(RemoteExecutionTemplate):
    pass


@pytest.fixture
def test_obj():
    return TestClass()


test_data = [(None, None, None, InvalidHostException),
             (Host(), None, None, InvalidUserException),
             (Host(), User(), None, InvalidClientException)]


@pytest.mark.parametrize("host, user, client, exception", test_data,
                         ids=["invalid_host_exception", "invalid_user_exception", "invalid_client_exception"])
def test_create_connection_raises(test_obj, host, user, client, exception):
    with pytest.raises(exception):
        test_obj.create_connection(host, user, client)


def test_connect_raises_not_implemented_error(test_obj):
    with pytest.raises(NotImplementedError):
        test_obj.connect(None)


def test_close_connection_raises_not_implemented_error(test_obj):
    with pytest.raises(NotImplementedError):
        test_obj.close_connection(None)


test_data = [(Host(), User(username="tester"), ConnectionNotFound),
             (Host(), None, InvalidUserException),
             (None, User(), InvalidHostException)]


@pytest.mark.parametrize("host, user, exception", test_data,
                         ids=["connection_not_found", "invalid_user_exception", "invalid_host_exception"])
def test_get_connection_raises(test_obj, host, user, exception):
    with pytest.raises(exception):
        test_obj.get_connection(host, user)


def test_get_connection(test_obj):
    host = Host()
    user = User()
    test_obj.conn = test_obj.create_connection(host, user, "empty")
    output_con = test_obj.get_connection(host=host, user=user)
    assert output_con == test_obj.conn
