import pytest

from networkobjects.connection import Connection
from networkobjects.host import Host
from networkobjects.user import User


@pytest.fixture(autouse=True)
def clear_pools():
    if hasattr(User, "__pool__"):
        User.__pool__.clear()
    if hasattr(Connection, "__pool__"):
        Connection.__pool__.clear()
    if hasattr(Host, "__pool__"):
        Host.__pool__.clear()
