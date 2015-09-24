import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
from server.main.client import Client
import components.main.filters.my_filter
import pytest
from tornado import gen
from server.main import coroutines
broadcast = coroutines.broadcast

cl = Client(Mock())

@pytest.mark.gen_test
def test_before_none_in_wihtout_limit():
    before = None
    model = {'id': '0', 'x': 8}
    cl.filters = {}
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10})

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=True, model_before=before, deleted=False, model=model)
    assert put.called
    assert call({'id': '0', 'x': 8}) in put.mock_calls
    assert len(put.mock_calls) == 1


@pytest.mark.gen_test
def test_before_none_out_wihtout_limit():
    before = None
    model = {'id': '0', 'x': 80}
    cl.filters = {}
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10})

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=True, model_before=before, deleted=False, model=model)
    assert not put.called


@pytest.mark.gen_test
def test_in_in_wihtout_limit():
    before = {'id': '0', 'x': 9}
    model = {'id': '0', 'x': 8}
    cl.filters = {}
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10})

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=False, model_before=before, deleted=False, model=model)
    assert put.called
    assert call({'id': '0', 'x': 8}) in put.mock_calls
    assert len(put.mock_calls) == 1


@pytest.mark.gen_test
def test_out_in_wihtout_limit():
    before = {'id': '0', 'x': 0}
    model = {'id': '0', 'x': 8}
    cl.filters = {}
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10})

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=False, model_before=before, deleted=False, model=model)
    assert put.called
    assert call({'id': '0', 'x': 8}) in put.mock_calls
    assert len(put.mock_calls) == 1


@pytest.mark.gen_test
def test_in_out_wihtout_limit():
    before = {'id': '0', 'x': 8}
    model = {'id': '0', 'x': 0}
    cl.filters = {}
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10})

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=False, model_before=before, deleted=False, model=model)
    assert put.called
    assert call({'id': '0', 'x': 0}) in put.mock_calls
    assert len(put.mock_calls) == 1


@pytest.mark.gen_test
def test_out_out_wihtout_limit():
    before = {'id': '0', 'x': -1}
    model = {'id': '0', 'x': 0}
    cl.filters = {}
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10})

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=False, model_before=before, deleted=False, model=model)
    assert not put.called
    assert len(put.mock_calls) == 0

# ######################

@pytest.mark.gen_test
def test_in_in():
    before = {'id': '0', 'x': 9}
    model = {'id': '0', 'x': 8}
    cl.filters = {}
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2})

    @gen.coroutine
    def side_effect(arg):
        return [{'id': '1', 'x': 8}, {'id': '0', 'x': 8}]
    coroutines.do_find = side_effect

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=False, model_before=before, deleted=False, model=model)
    assert put.called
    assert call({'id': '0', 'x': 8}) in put.mock_calls
    assert len(put.mock_calls) == 1


@pytest.mark.gen_test
def test_in_out_of_limit():
    before = {'id': '0', 'x': 9}
    model = {'id': '0', 'x': 6}
    cl.filters = {}
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2})

    @gen.coroutine
    def side_effect(arg):
        return [{'id': '1', 'x': 8}, {'id': '2', 'x': 7}]
    coroutines.do_find = side_effect

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=False, model_before=before, deleted=False, model=model)
    assert put.called
    assert call({'id': '0', 'x': 6}) in put.mock_calls
    assert call({'id': '2', 'x': 7}) in put.mock_calls


@pytest.mark.gen_test
def test_in_out_of_filter():
    before = {'id': '0', 'x': 9}
    model = {'id': '0', 'x': 0}
    cl.filters = {}
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2})

    @gen.coroutine
    def side_effect(arg):
        return [{'id': '1', 'x': 8}, {'id': '2', 'x': 7}]
    coroutines.do_find = side_effect

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=False, model_before=before, deleted=False, model=model)
    assert put.called
    assert call({'id': '0', 'x': 0}) in put.mock_calls
    assert call({'id': '2', 'x': 7}) in put.mock_calls

@pytest.mark.gen_test
def test_out_out_limit():
    before = {'id': '0', 'x': 0}
    model = {'id': '0', 'x': -1}
    cl.filters = {}
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2})

    @gen.coroutine
    def side_effect(arg):
        return [{'id': '1', 'x': 8}, {'id': '2', 'x': 7}]
    coroutines.do_find = side_effect

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=False, model_before=before, deleted=False, model=model)
    assert not put.called
    assert len(put.mock_calls) == 0

@pytest.mark.gen_test
def test_out_in_limit():
    before = {'id': '0', 'x': 0}
    model = {'id': '0', 'x': 9}
    cl.filters = {}
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2})

    @gen.coroutine
    def side_effect(arg):
        return [{'id': '0', 'x': 9}, {'id': '2', 'x': 7}]
    coroutines.do_find = side_effect

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=False, model_before=before, deleted=False, model=model)
    assert put.called
    assert call({'id': '0', 'x': 9}) in put.mock_calls
    assert len(put.mock_calls) == 1


@pytest.mark.gen_test
def test_new_in_limit():
    before = None
    model = {'id': '0', 'x': 9}
    cl.filters = {}
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2})

    @gen.coroutine
    def side_effect(arg):
        return [{'id': '0', 'x': 9}, {'id': '2', 'x': 7}]
    coroutines.do_find = side_effect

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=True, model_before=before, deleted=False, model=model)
    assert put.called
    assert call({'id': '0', 'x': 9}) in put.mock_calls
    assert len(put.mock_calls) == 1


@pytest.mark.gen_test
def test_new_out_limit():
    before = None
    model = {'id': '0', 'x': 99}
    cl.filters = {}
    cl.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter', 'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2})

    @gen.coroutine
    def side_effect(arg):
        return [{'id': '1', 'x': 9}, {'id': '2', 'x': 7}]
    coroutines.do_find = side_effect

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(collection='A', new=True, model_before=before, deleted=False, model=model)
    assert not put.called
    assert len(put.mock_calls) == 0

