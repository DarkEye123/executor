__author__ = 'mlesko'

import inspect


# TODO if there is some usability in this
class ModelRegistrator(type):
    def __register_class__(cls, bases):
        for parent in bases:
            if hasattr(parent, '__meta_set__'):
                parent.__meta_set__.add(cls)
                for base_class in inspect.getmro(parent):
                    if hasattr(base_class, '__meta_set__'):
                        base_class.__meta_set__ -= set(inspect.getmro(parent))
                    cls.__register_class__(inspect.getmro(base_class)[1:])

    def __init__(cls, cls_name, bases, nmspace):
        super(ModelRegistrator, cls).__init__(cls_name, bases, nmspace)

        # there can be cases where model is not from RemoteExecutionTemplate inheritance tree
        if not hasattr(cls, '__meta_set__'):
            cls.__meta_set__ = set()

        cls.__register_class__(bases)

    def __iter__(cls):
        return iter(cls.__meta_set__)
