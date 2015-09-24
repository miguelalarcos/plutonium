import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
from server.main.client import Client
import components.main.filters.my_filter
import pytest
from tornado import gen
from server.main import coroutines
broadcast = coroutines.broadcast


@pytest.mark.gen_test
def test_1():
    before = {'id': '0', 'x': 9}
    model = {'x': 10}
    cl = Client(Mock())
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2})

    @gen.coroutine
    def side_effect(arg):
        return [{'_id': '0', 'x': 8}, {'_id': '2', 'x': 7}]
    coroutines.do_find = side_effect

    put = Mock()
    @gen.coroutine
    def f(arg):
        put(arg)
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=False, model_before=before, deleted=False, model=model)
    assert put.called
