import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
from server.main.client import Client
import components.main.filters.my_filter
import pytest
from tornado import gen
from server.main import coroutines
from components.lib.filter_mongo import Filter
broadcast = coroutines.broadcast

#socket = Mock()
#Client.clients = {}
#cl = Client(socket)

filter = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2,
                                    '__skip__': 0})

@pytest.fixture
def clean():
    Client.clients = {}

@pytest.mark.gen_test
def test_broadcas_1(monkeypatch, clean):
    socket = Mock()
    cl = Client(socket)
    print('-->', Client.clients)
    cl.filters = {}
    cl.add_filter(filter)
    print('-->', cl.filters)
    model = {'id': '0', 'x': 8, '__collection__': 'A'}

    do_find = Mock()
    @gen.coroutine
    def f(*args, **kw):
        do_find(*args, **kw)
        return [{'id': '0'}]
    #coroutines.do_find = f
    monkeypatch.setattr(coroutines, 'do_find', f)

    put = Mock()
    @gen.coroutine
    def fput(arg):
        put(arg[1])
        return None
    monkeypatch.setattr(coroutines.q_send, 'put', fput)
    #coroutines.q_send = Mock()
    #coroutines.q_send.put = fput

    yield broadcast(model)

    assert do_find.called
    assert put.called
    print(put.mock_calls)
    assert call({'id': '0', 'x': 8, '__collection__': 'A', '__skip__': '0', '__filter__':  filter.full_name}) in put.mock_calls

"""
@pytest.mark.gen_test
def test_before_none_in_wihtout_limit():
    before = None
    model = {'id': '0', 'x': 8, '__collection__': 'A'}
    cl.filters = {}
    cl.add_filter(filter)

    put = Mock()
    @gen.coroutine
    def f(arg):
        print('arg', arg[1])
        put(arg[1])
        return None
    coroutines.q_send = MagicMock()
    coroutines.q_send.put = f

    yield broadcast(item=model)
    assert put.called
    assert call({'id': '0', 'x': 8}) in put.mock_calls
    assert len(put.mock_calls) == 1


@pytest.mark.gen_test
def test_before_none_out_wihtout_limit():
    before = None
    model = {'id': '0', 'x': 80}
    cl.filters = {}
    cl.add_filter(filter)

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
    cl.add_filter(filter)

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
    cl.add_filter(filter)

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
    cl.add_filter(filter)

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
    cl.add_filter(filter)

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
    cl.add_filter(filter)

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
    cl.add_filter(filter)

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
    cl.add_filter(filter)

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
    cl.add_filter(filter)

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
    cl.add_filter(filter)

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
    cl.add_filter(filter)

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
    cl.add_filter(filter)

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
"""
