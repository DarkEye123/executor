class SingletonWrapper(type):
    __active_instances = dict()

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__active_instances:
            cls.__active_instances[cls] = super(SingletonWrapper, cls).__call__(*args, **kwargs)
        return cls.__active_instances[cls]
