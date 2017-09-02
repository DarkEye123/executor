__author__ = 'mlesko'
from executor_exceptions import *
from metaclasses.singleton_wrapper import SingletonWrapper
from networkobjects.connection import Connection
from networkobjects.host import Host
from networkobjects.user import User
from . import logger


class RemoteExecutionTemplate(object):
    """
    Template for all possible model_tests in the future. Contain methods that needs to be inherited and implemented and
    expanded by the functionality of child model.
    """
    # __metaclass__ = ModelRegistrator
    __metaclass__ = SingletonWrapper

    # __meta_set__ = set()  # set used by metaclass to model registration

    def __init__(self):
        pass

    def connect(self, connection):
        """
        Connects via underlying module using specified connection object.
        If connection object was already connected connecting is skipped.
        @param connection: connection object to be used
        @type connection: Connection
        @warning: this method needs to be implemented in the child class
        @raise NotImplementedError:
        @return: None
        @rtype: None
        """
        raise NotImplementedError

    def close_connection(self, connection=None):
        """
        Closes connection - invalidates it for further usage
        In case an connection is not provided the active connection will be closed
        @param connection: connection to be closed
        @type connection: Connection
        @warning: this method needs to be implemented in the child class
        @raise NotImplementedError:
        @return: None
        @rtype: None
        """
        raise NotImplementedError

    def create_connection(self, host, user, client):
        """
        Create connection and returns it.
        Created connection is added automatically to the the pool of connections.
        @param host: host object
        @type host: Host
        @param user: user object of type
        @type user: User
        @param client: underlying client integrated by the model, or its subclass
        @type client: any
        @warning: Please be sure that client is initialized in the time of the method call
        @return: created connection
        @rtype: Connection
        """
        if not isinstance(host, Host):
            raise InvalidHostException("host must be an instance of the Host class")
        if not isinstance(user, User):
            raise InvalidUserException("user must be an instance of the User class")
        if client is None:
            raise InvalidClientException("Integrated Client during connection creation can't be None")
        connection = Connection(host=host, user=user, client=client)
        return connection

    def get_connection(self, host=None, user=None):
        """
        Get connection object from the pool of connections. Note that B{host} and B{user} are used only when B{cid} is I{None}
        @param host: host object
        @type host: Host
        @param user: user object
        @type user: User
        @warning: B{host} and B{user} are used only when B{c_id} is I{None}
        @raise InvalidHostException:
        @raise InvalidUserException:
        @raise ConnectionNotFound: if connection was not found in the pool of connections
        @return: connection object from the pool of connections.
        @rtype: Connection
        """
        if not isinstance(host, Host):
            raise InvalidHostException("host must be an instance of the Host class")
        if not isinstance(user, User):
            raise InvalidUserException("user must be an instance of the User class")
        connection = Connection.find(host, user)
        if connection is None:
            logger.debug("Connection: %s was not found" % (Connection.generate_id(host, user),))
            raise ConnectionNotFound
        return connection
