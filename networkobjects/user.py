__author__ = 'mlesko'

import executor_exceptions
from network_object import NetworkObject
from . import logger


class User(NetworkObject):
    """
    Represents an User associated which is authorized for remote control.
    Contains necessary authentication data. In further releases it may be
    updated for more ways how to provide identification.
    """

    def __new__(cls, username="root", password=None):  # this is due to proper id generation in network object
        """
        Hos is created and identified by a user and his password.
        If user already exists in the container of the class, creation and initialization
        of a new one is omitted and the existing one is returned.
        @param username: username for authentication
        @type username: str
        @param password: password for login
        @type password: str
        @return: User instance
        @rtype: User
        """
        cls.__check_parameters(username=username)
        return super(User, cls).__new__(cls, username=username, password=password)

    def __init__(self, username="root", password=None):
        """

        Hos is created and identified by a user and his password.
        If user already exists in the container of the class, initialization
        of a new one is omitted and the existing one is returned.
        @param username: username for authentication
        @type username: str
        @param password: password for login
        @type password: str
        """
        _id = User.generate_id(username=username, password=password)
        if not hasattr(User, "__pool__") or not User.__pool__.has_key(_id):  # do init only if it is new object
            self.username = username
            self.password = password
            self.id = _id
            self.connections = set()  # list is not appropriate due to possible high redundancy of same connections
            super(User, self).__init__(self.id)
            logger.debug('Created %s' % self)

    def __str__(self):
        return "%s object: %s with connection list:\n%s" % (self.__class__.__name__, self.id, self.connections)

    @classmethod
    def __check_parameters(cls, username):
        if not isinstance(username, basestring):
            raise executor_exceptions.InvalidUsernameExeption("username must be string")

    @classmethod
    def generate_id(cls, username, password):
        """
        Generates ID from username and password.
        @type username: str
        @type password: str
        @return: generated ID
        @rtype: str
        """
        cls.__check_parameters(username=username)
        return User._generate_id(username=username, password=password)

    @classmethod
    def _generate_id(cls, *args, **kwargs):
        """
        Should not be used directly.
        """
        if args != () or kwargs != {}:
            if kwargs != {}:
                username = kwargs.get("username")  # "or" is not used here due to possible None value in dict
                password = kwargs.get("password")
            else:
                username = args[0]
                password = args[1]
            return "%s:%s" % (username, password)
