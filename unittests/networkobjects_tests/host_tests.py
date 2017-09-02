import pytest

from networkobjects.host import Host
from executor_exceptions import *

test_data = [(InvalidAddress, dict({"address": None})),
             (InvalidPortValue, dict({"port": -1})),
             (InvalidPortValue, dict({"port": 65536})),
             (InvalidPortValue, dict({"port": "1"}))
             ]


@pytest.mark.parametrize("exception, data", test_data,
                         ids=["invalid_address", "invalid_port_value_min",
                              "invalid_port_value_max", "invalid_port_type"])
def test_host_create_raises(exception, data):
    with pytest.raises(exception):
        Host(**data)


def test_host_create_only_once():
    conn1 = "false_conn1"
    conn2 = "false_conn2"
    host = Host()
    host.connections.add(conn1)
    host.connections.add(conn2)
    host = Host()  # returns previously created host object
    assert len(host.connections)
    assert host.connections.pop() == conn1
    assert host.connections.pop() == conn2


test_data = [(InvalidAddress, dict({"address": None, "port": 22})),
             (InvalidPortValue, dict({"address": "addr", "port": -1})),
             (InvalidPortValue, dict({"address": "addr", "port": 65536})),
             (InvalidPortValue, dict({"address": "addr", "port": "65536"}))
             ]


@pytest.mark.parametrize("exception, data", test_data,
                         ids=["invalid_address", "invalid_port_value_min",
                              "invalid_port_value_max", "invalid_port_type"])
def test_host_generate_id_public_raises(exception, data):
    with pytest.raises(exception):
        Host.generate_id(**data)


def test_host_generate_id_public():
    address = "test_addr"
    port = 22
    sim_id = "%s:%s" % (address, port)
    host = Host(address=address, port=port)
    gen_id = Host.generate_id(address=address, port=port)
    assert host.id == gen_id
    assert gen_id == sim_id


def test_host_generate_id_protected():
    address = "test_addr"
    port = 22
    sim_id = "%s:%s" % (address, port)
    host = Host(address=address, port=port)
    gen_id = Host._generate_id(address=address, port=port)
    assert host.id == gen_id
    assert gen_id == sim_id
