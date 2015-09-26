import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
import pytest
from tornado import gen
from server.main import coroutines
from server.main.client import Client
from components.main.models import A
import components.main.filters.my_filter
from components.lib.filter_mongo import Filter

handle = coroutines.handle_collection
q_send = Mock()

@gen.coroutine
def fq(*args, **kw):
    q_send(*args, **kw)
    return
coroutines.q_send.put = fq


@pytest.fixture(scope="module")
def client():
    Client.clients = {}
    socket = Mock()
    cl = Client(socket)
    return cl

@pytest.mark.gen_test
def test_update_collection_in_and_in(monkeypatch, client):
    db = MagicMock()
    monkeypatch.setattr(coroutines, 'db', db)
    q_send.reset_mock()

    item = {'__client__': None, '__collection__':'A', 'id': '0', 'x': 8}
    #client.filters = {}
    filt = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2,
                                    '__skip__': 0})
    client.add_filter(filt)

    filter_full_name = filt.full_name
    ret = [[{'_id': '0'}, {'_id': '1'}], [{'_id': '0'}, {'_id': '1'}]]

    to_list = Mock()
    @gen.coroutine
    def f(length):
        to_list(length)
        return ret.pop(0)

    find_one = Mock()
    @gen.coroutine
    def g(arg):
        find_one(arg)
        ret = {}
        ret['0'] = {'_id': '0', 'x': 9}
        ret['1'] = None
        ret['2'] = {'_id': '2', 'x': 7}
        return ret[arg['_id']]

    update = Mock()
    @gen.coroutine
    def h(id, arg):
        update(id, arg)
        return

    db['A'].find_one = g
    db['A'].find().to_list = f
    db['A'].update = h

    yield handle(item)
    assert find_one.called
    assert to_list.called
    assert q_send.called
    assert call((client.socket, {'__skip__': '0', '__filter__': filter_full_name, 'id': '0', 'x': 8, '__collection__': 'A'})) in q_send.mock_calls
    assert len(q_send.mock_calls) == 1


@pytest.mark.gen_test
def test_update_collection_in_and_out(monkeypatch, client):
    db = MagicMock()
    monkeypatch.setattr(coroutines, 'db', db)
    q_send.reset_mock()

    item = {'__client__': None, '__collection__':'A', 'id': '0', 'x': 6}

    filt = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2,
                                    '__skip__': 0})
    client.add_filter(filt)

    ret = [[{'_id': '0'}, {'_id': '1'}], [{'_id': '1'}, {'_id': '2'}]]

    to_list = Mock()
    @gen.coroutine
    def f(length):
        to_list(length)
        return ret.pop(0)

    find_one = Mock()
    @gen.coroutine
    def g(arg):
        find_one(arg)
        ret = {}
        ret['0'] = {'_id': '0', 'x': 9}
        ret['1'] = None
        ret['2'] = {'_id': '2', 'x': 7}
        return ret[arg['_id']]

    update = Mock()
    @gen.coroutine
    def h(id, arg):
        update(id, arg)
        return

    db['A'].find_one = g
    db['A'].find().to_list = f
    db['A'].update = h

    yield handle(item)
    assert find_one.called
    assert to_list.called
    assert q_send.called
    assert call((client.socket, {'__skip__': '1', '__filter__': filt.full_name, '__collection__': 'A', 'id': '2', 'x': 7})) in q_send.mock_calls
    assert len(q_send.mock_calls) == 1


@pytest.mark.gen_test
def test_update_collection_out_and_out(monkeypatch, client):
    db = MagicMock()
    monkeypatch.setattr(coroutines, 'db', db)
    q_send.reset_mock()

    item = {'__client__': None, '__collection__':'A', 'id': '0', 'x': -1}
    #client.filters = {}
    filt = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2,
                                    '__skip__': 0})
    client.add_filter(filt)

    ret = [[{'_id': '1'}, {'_id': '2'}], [{'_id': '1'}, {'_id': '2'}]]

    to_list = Mock()
    @gen.coroutine
    def f(length):
        to_list(length)
        return ret.pop(0)

    find_one = Mock()
    @gen.coroutine
    def g(arg):
        find_one(arg)
        ret = {}
        ret['0'] = {'_id': '0', 'x': -2}
        ret['1'] = None
        ret['2'] = {'_id': '2', 'x': 7}
        return ret[arg['_id']]

    update = Mock()
    @gen.coroutine
    def h(id, arg):
        update(id, arg)
        return

    db['A'].find_one = g
    db['A'].find().to_list = f
    db['A'].update = h

    yield handle(item)
    assert not q_send.called
    assert len(q_send.mock_calls) == 0

@pytest.mark.gen_test
def test_update_collection_out_and_in(monkeypatch, client):
    db = MagicMock()
    monkeypatch.setattr(coroutines, 'db', db)
    q_send.reset_mock()

    item = {'__client__': None, '__collection__':'A', 'id': '0', 'x': 6}
    #client.filters = {}
    filt = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2,
                                    '__skip__': 0})
    client.add_filter(filt)

    ret = [[{'_id': '1'}, {'_id': '2'}], [{'_id': '2'}, {'_id': '0'}]]

    to_list = Mock()
    @gen.coroutine
    def f(length):
        to_list(length)
        return ret.pop(0)

    find_one = Mock()
    @gen.coroutine
    def g(arg):
        find_one(arg)
        ret = {}
        ret['0'] = {'_id': '0', 'x': -2}
        ret['1'] = None
        ret['2'] = {'_id': '2', 'x': 7}
        return ret[arg['_id']]

    update = Mock()
    @gen.coroutine
    def h(id, arg):
        update(id, arg)
        return

    db['A'].find_one = g
    db['A'].find().to_list = f
    db['A'].update = h

    yield handle(item)
    assert q_send.called
    assert call((client.socket, {'__skip__': '2', '__filter__': filt.full_name, '__collection__': 'A', 'id': '0', 'x': 6})) in q_send.mock_calls
    assert len(q_send.mock_calls) == 1


@pytest.mark.gen_test
def test_before_is_None_after_is_in(monkeypatch, client):
    db = MagicMock()
    monkeypatch.setattr(coroutines, 'db', db)
    q_send.reset_mock()

    item = {'__client__': None, '__collection__':'A', 'id': '0', 'x': 6}
    #client.filters = {}
    filt = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2,
                                    '__skip__': 0})
    client.add_filter(filt)

    ret = [[{'_id': '1'}, {'_id': '2'}], [{'_id': '2'}, {'_id': '0'}]]

    to_list = Mock()
    @gen.coroutine
    def f(length):
        to_list(length)
        return ret.pop(0)

    find_one = Mock()
    @gen.coroutine
    def g(arg):
        find_one(arg)
        ret = {}
        ret['0'] = None
        ret['1'] = None
        ret['2'] = None  # {'_id': '2', 'x': 7}
        return ret[arg['_id']]

    insert = Mock()
    @gen.coroutine
    def h(arg):
        insert(arg)
        return

    db['A'].find_one = g
    db['A'].find().to_list = f
    db['A'].insert = h

    yield handle(item)
    assert insert.called
    assert q_send.called
    assert call((client.socket, {'__skip__': '2', '__filter__': filt.full_name, '__collection__': 'A', 'id': '0', 'x': 6})) in q_send.mock_calls
    assert len(q_send.mock_calls) == 1

