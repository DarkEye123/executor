__author__ = 'mlesko'

import copy


class CIterator(type):
    def __iter__(cls):
        if hasattr(cls, '__iterable_target__'):
            if hasattr(cls.__iterable_target__,
                       'itervalues'):  # can have iteritems, but instance doesn't have to be a dict subclass
                copied_iterable = copy.copy(cls.__iterable_target__.values())
            else:
                copied_iterable = copy.copy(cls.__iterable_target__)
            return iter(copied_iterable)
        return cls

    def next(cls):
        raise StopIteration()

    def __len__(cls):
        return len(cls.__iterable_target__)
