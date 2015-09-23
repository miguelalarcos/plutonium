from server.main.client import Client
from server.main.coroutines import handle_filter
from server.main import coroutines
from mock import MagicMock, call

db = coroutines.db = MagicMock()

Client('0')


def test_handle_filter():
    item = {'__client__': '0', '__filter__': 'my_filter', 'x': 5, 'y': 10}

    handle_filter(item)
    assert call('A') in db.__getitem__.mock_calls
    assert call({'x': {'$gt': 5, '$lt': 10}}) in db.__getitem__().find.mock_calls
