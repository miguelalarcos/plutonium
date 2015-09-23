import sys
sys.path.insert(0, '.')
from server.main.client import Client
from server.main.coroutines import handle_filter, handle_collection
from server.main import coroutines
from mock import Mock, MagicMock, call
from tornado import gen
import pytest

db = coroutines.db = MagicMock()

Client('0')


def _test_handle_filter():
    item = {'__client__': '0', '__filter__': 'my_filter', 'x': 5, 'y': 10}

    handle_filter(item)
    assert call('A') in db.__getitem__.mock_calls
    assert call({'x': {'$gt': 5, '$lt': 10}}) in db.__getitem__().find.mock_calls


@pytest.mark.gen_test
def test_handle_collection():
    item = {'__client__': '0', '__collection__': 'A', 'x': 10, 'id': '1'}

    insert = Mock()
    find_one = Mock()
    @gen.coroutine
    def f(arg):
        find_one(arg)
        return None

    @gen.coroutine
    def g(arg):
        insert(arg)
        return '1'

    db = MagicMock()
    coroutines.db = db
    db['A'].find_one = f
    db['A'].insert = g

    yield handle_collection(item)

    assert find_one.called
    assert call({'_id': '1'}) in find_one.mock_calls
    assert insert.called
    assert call({'_id': '1', 'x': 10}) in insert.mock_calls
