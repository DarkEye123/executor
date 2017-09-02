__author__ = 'mlesko'

import executor_exceptions
from network_object import NetworkObject
from . import logger


class Host(NetworkObject):
    """
    Represent remote machine to connect to.
    Every host is unique and specified by its address and port. If there is an attempt to create
    the host with the same identifier as already exists, this existing host is returned instead.
    """

    def __new__(cls, address='localhost', port=22):  # this is due to proper id generation in network object
        """
        In a case of the already created host (same address and a port) this one will be returned
        without further initialisation.
        @param address: address that will be used for data transfers
        @type address: str
        @param port: port to be used by ssh client
        @type port: int
        @return: unique host object (empty)
        @rtype: Host
        """
        cls.__check_parameters(address, port)
        return super(Host, cls).__new__(cls, address=address, port=port)

    def __init__(self, address='localhost', port=22):
        """
        In a case of already initialized host the initialization is skipped.
        @param address: address that will be used for data transfers
        @type address: str
        @param port: port to be used by ssh client
        @type port: int
        """
        _id = Host.generate_id(address=address, port=port)
        if not hasattr(Host, "__pool__") or not Host.__pool__.has_key(_id):  # do init only if it is new object
            self.address = address
            self.port = port
            self.id = _id
            self.connections = set()  # list is not appropriate due to possible high redundancy of same connections
            super(Host, self).__init__(self.id)
            logger.debug('Created %s' % self)

    def __str__(self):
        return "%s object: %s with connection list:\n%s" % (self.__class__.__name__, self.id, self.connections)

    @classmethod
    def __check_parameters(cls, address, port):
        if not isinstance(address, basestring):
            raise executor_exceptions.InvalidAddress("address must be string")
        if not isinstance(port, int):
            raise executor_exceptions.InvalidPortValue("Port must be integer")
        if port < 0 or port > 65535:
            raise executor_exceptions.InvalidPortValue("Port should be in range: <0, 65535>")

    @classmethod
    def generate_id(cls, address, port):
        """
        Generates ID from address and port.
        @type address: str
        @type port: str
        @return: generated ID
        @rtype: str
        """
        cls.__check_parameters(address, port)
        return Host._generate_id(address=address, port=port)

    @classmethod
    def _generate_id(cls, *args, **kwargs):
        """
        This method B{should not} be used directly. Use L{generate_id} instead.
        """
        # do not use this method directly
        if args != () or kwargs != {}:
            if kwargs != {}:
                address = kwargs.get("address")  # "or" is not used here due to possible None value in dict
                port = kwargs.get("port")
            else:
                address = args[0]
                port = args[1]
            return "%s:%s" % (address, port)
