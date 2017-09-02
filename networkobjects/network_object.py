import executor_exceptions
from executor_exceptions import *

__author__ = 'mlesko'

from metaclasses.class_iterator import CIterator
from . import logger


class NetworkObject(object):
    """
    Provides common functionality for objects used during networking.
    Typically it means that when you have user already as an object you do not need a second one which is the same.
    Same applies for hosts and connection. Therefore, every of these classes share common trait.

    Common idea is to provide a container for every such class to track its unique objects.
    These objects have unique ID  and if such object is already present in this container, it is
    simply returned instead of the creation of a new one.

    Another common trait is that these classes are iterable. It means it is possible to iterate over each
    child class of this base class.

      >>> for connection in Connection:
      >>>   print connection

    container initialization and iteration target setting is made in __new__ and __init__ methods.
    This ensures that chane in this common functionality is made only on the one place.
    """
    __metaclass__ = CIterator

    # __pool__ = WeakValueDictionary()  # for base class it is only template attribute
    # __pool__ = dict()  # for base class it is only template attribute
    # __iterable_target__ = __pool__  # for base class it is only template attribute

    def __new__(cls, *args, **kwargs):
        """
        Ensure that if '__pool__' attribute is present in the child class, a possible object according to the generated id
        is returned or created a new one
        """
        if hasattr(cls, "__pool__"):  # if there is no pool, then no objects were made
            object_id = cls._generate_id(*args, **kwargs)
            instance = cls.__pool__.get(object_id)
            if instance is not None:
                return instance  # return already created instance
        return super(NetworkObject, cls).__new__(cls)

    def __init__(self, object_id):
        """
        If class does not have a container '__pool__' for storing its unique instances, it is created.
        Also, it ensures that '__pool__' container is filled with newly created instances if they are not present.
        When the container is created it makes also child class iterable.
        @param object_id: id of the instance
        @type object_id: str
        """

        if not hasattr(self.__class__, "__pool__"):
            logger.debug(
                "Settting container for objects of class: %s" % self.__class__)
            self.__class__.__pool__ = dict()  # for every child class create its own pool
            logger.debug(
                "Settting class: %s to be iterable" % self.__class__)
            self.__class__.__iterable_target__ = self.__class__.__pool__  # this pool with registered object is used for iterations

        if not self.__class__.__pool__.has_key(object_id):  # if it is new object add it to the pool
            logger.debug(
                "Adding object: '%s' of to container of the class: %s" % (object_id, self.__class__))
            self.__class__.__pool__[object_id] = self

    def __str__(self):
        """
        Every child class has its own string representation, but to remove redundant definition
        a special attribute '_desc' is present to ensure same semantic for its representation.
        """
        if hasattr(self, '_desc'):
            return "%s: %s" % (self.__class__, self._desc)
        return str(self.__dict__)

    @classmethod
    def _generate_id(cls, *args, **kwargs):
        """
        This is method for ID generation, it ensures that it will be implemented in the child with same semantic
        @raise exceptions.NotImplementedError:
        """
        raise executor_exceptions.NotImplementedError
