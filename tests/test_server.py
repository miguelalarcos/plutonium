from .. import server
from mock import Mock, MagicMock, call
from ..server import Client, handle_filter

server.db = MagicMock()
db = server.db

Client('0')


def test_handle_filter():
    item = {'__client__': '0', '__filter__': 'my_filter', 'x': 5, 'y': 10}

    handle_filter(item)
    assert call('A') in db.__getitem__.mock_calls
    assert call({'x': {'$gt': 5, '$lt': 10}}) in db.__getitem__().find.mock_calls
