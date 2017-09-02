import pytest

from metaclasses.class_iterator import CIterator


@pytest.fixture(autouse=True)
def reset():
    TestClassList.__iterable_target__ = []
    TestClassSet.__iterable_target__ = set()
    TestClassDict.__iterable_target__ = {}


class TestClassList(object):
    __metaclass__ = CIterator
    __iterable_target__ = []

    def __init__(self, value):
        self.value = value
        TestClassList.__iterable_target__.append(self)


class TestClassSet(object):
    __metaclass__ = CIterator
    __iterable_target__ = set()

    def __init__(self, value):
        self.value = value
        TestClassSet.__iterable_target__.add(self)


class TestClassDict(object):
    __metaclass__ = CIterator
    __iterable_target__ = {}

    def __init__(self, value):
        self.value = value
        TestClassDict.__iterable_target__[value] = self


def test_class_iterable_list_store():
    pool_values = [1, 2, 3]
    for value in pool_values:
        TestClassList(value)

    assert len(pool_values) == len(TestClassList.__iterable_target__)
    for x in xrange(len(pool_values)):
        assert pool_values[x] == TestClassList.__iterable_target__[x].value


def test_class_iterable_list_iterable():
    pool_values = [1, 2, 3]

    for value in pool_values:
        TestClassList(value)

    for obj in TestClassList:
        assert obj.value in pool_values
        pool_values.remove(obj.value)

    assert len(pool_values) == 0


def test_class_iterable_set_store():
    pool_values = [1, 2, 3]
    for value in pool_values:
        TestClassSet(value)

    assert len(pool_values) == len(TestClassSet.__iterable_target__)


def test_class_iterable_set_iterable():
    pool_values = [1, 2, 3]

    for value in pool_values:
        TestClassSet(value)

    for obj in TestClassSet:
        assert obj.value in pool_values
        pool_values.remove(obj.value)

    assert len(pool_values) == 0


def test_class_iterable_dict_store():
    pool_values = [1, 2, 3]
    for value in pool_values:
        TestClassDict(value)

    assert len(pool_values) == len(TestClassDict.__iterable_target__)
    for x in pool_values:
        assert x == TestClassDict.__iterable_target__[x].value


def test_class_iterable_dict_iterable():
    pool_values = [1, 2, 3]

    for value in pool_values:
        TestClassDict(value)

    for obj in TestClassDict:
        assert obj.value in pool_values
        pool_values.remove(obj.value)

    assert len(pool_values) == 0


test_data = [TestClassList, TestClassSet, TestClassDict]


@pytest.mark.parametrize("cls", test_data, ids=["list", "set", "dict"])
def test_object_in_class(cls):
    pool_values = [1, 2, 3]
    for value in pool_values:
        cls(value)

    for obj in cls:
        assert obj in cls  # this ensures usage of such construct
