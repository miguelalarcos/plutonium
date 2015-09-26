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

filter = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2,
                                    '__skip__': 0})

@pytest.fixture
def client():
    Client.clients = {}
    socket = Mock()
    cl = Client(socket)
    return cl


@pytest.mark.gen_test
def test_broadcas_the_model_in_after(monkeypatch, client):
    cl = client
    cl.add_filter(filter)
    model = {'id': '0', 'x': 8, '__collection__': 'A'}

    do_find = Mock()
    @gen.coroutine
    def f(*args, **kw):
        do_find(*args, **kw)
        return [{'id': '0'}, {'id': '1'}]
    monkeypatch.setattr(coroutines, 'do_find', f)

    put = Mock()
    @gen.coroutine
    def fput(arg):
        put(arg[1])
        return None
    monkeypatch.setattr(coroutines.q_send, 'put', fput)

    yield broadcast(model)

    assert do_find.called
    assert put.called
    print(put.mock_calls)
    assert call({'id': '0', 'x': 8, '__collection__': 'A', '__skip__': '0', '__filter__':  filter.full_name}) in put.mock_calls
    assert len(put.mock_calls) == 1


@pytest.mark.gen_test
def test_broadcas_the_model_not_in_after_but_after_item_not_in_before(monkeypatch, client):
    cl = client
    cl.add_filter(filter)
    filter.before = ['2']
    model = {'id': '0', 'x': 8, '__collection__': 'A'}

    do_find = Mock()
    @gen.coroutine
    def f(*args, **kw):
        do_find(*args, **kw)
        return [{'id': '1'}, {'id': '2'}]
    monkeypatch.setattr(coroutines, 'do_find', f)

    put = Mock()
    @gen.coroutine
    def fput(arg):
        put(arg[1])
        return None
    monkeypatch.setattr(coroutines.q_send, 'put', fput)

    do_find_one = Mock()
    @gen.coroutine
    def f_do_find_one(*args, **kw):
        do_find_one(*args, **kw)
        return {'id': '1', 'x': 8, '__collection__': 'A'}
    monkeypatch.setattr(coroutines, 'do_find_one', f_do_find_one)

    yield broadcast(model)

    assert do_find.called
    assert do_find_one.called
    assert put.called
    assert call({'id': '1', 'x': 8, '__collection__': 'A', '__skip__': '1', '__filter__':  filter.full_name}) in put.mock_calls
    assert len(put.mock_calls) == 1

@pytest.mark.gen_test
def test_broadcas_after_is_empty(monkeypatch, client):
    cl = client
    cl.add_filter(filter)
    filter.before = ['2']
    model = {'id': '0', 'x': 8, '__collection__': 'A'}

    do_find = Mock()
    @gen.coroutine
    def f(*args, **kw):
        do_find(*args, **kw)
        return []
    monkeypatch.setattr(coroutines, 'do_find', f)

    put = Mock()
    @gen.coroutine
    def fput(arg):
        put(arg[1])
        return None
    monkeypatch.setattr(coroutines.q_send, 'put', fput)

    do_find_one = Mock()
    @gen.coroutine
    def f_do_find_one(*args, **kw):
        do_find_one(*args, **kw)
        return {'id': '1', 'x': 8, '__collection__': 'A'}
    monkeypatch.setattr(coroutines, 'do_find_one', f_do_find_one)

    yield broadcast(model)

    assert not put.called

@pytest.mark.gen_test
def test_broadcas_after_yet_in_before(monkeypatch, client):
    cl = client
    cl.add_filter(filter)
    filter.before = ['1', '2']
    model = {'id': '0', 'x': 8, '__collection__': 'A'}

    do_find = Mock()
    @gen.coroutine
    def f(*args, **kw):
        do_find(*args, **kw)
        return [{'id': '1'}, {'id': '2'}]
    monkeypatch.setattr(coroutines, 'do_find', f)

    put = Mock()
    @gen.coroutine
    def fput(arg):
        put(arg[1])
        return None
    monkeypatch.setattr(coroutines.q_send, 'put', fput)

    do_find_one = Mock()
    @gen.coroutine
    def f_do_find_one(*args, **kw):
        do_find_one(*args, **kw)
        return None
    monkeypatch.setattr(coroutines, 'do_find_one', f_do_find_one)

    yield broadcast(model)

    assert not put.called