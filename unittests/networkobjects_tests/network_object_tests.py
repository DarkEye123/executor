import pytest

from executor_exceptions import NotImplementedError
from networkobjects.network_object import NetworkObject


# NetworkObject should be abstract
class TestClass(NetworkObject):
    @classmethod
    def _generate_id(cls, *args, **kwargs):
        return args[0]


@pytest.fixture(autouse=True)
def reset():
    if hasattr(TestClass, "__pool__"):
        TestClass.__pool__.clear()


def test_pool_creation():
    assert hasattr(TestClass, "__pool__") == False
    TestClass(1)
    assert hasattr(TestClass, "__pool__") == True


def test_generate_id_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        NetworkObject._generate_id()


def test_create_only_once():
    test_obj1 = TestClass(1)
    test_obj2 = TestClass(1)
    assert id(test_obj1) == id(test_obj2)
