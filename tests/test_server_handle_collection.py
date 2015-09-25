import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
import pytest
from tornado import gen
from server.main import coroutines
from server.main.client import Client
from components.main.models import A
import components.main.filters.my_filter

handle = coroutines.handle_collection
handle2 = coroutines.handle_collection2
client = Client(Mock())


@pytest.fixture(scope="module")
def set_db():
    db = MagicMock()
    coroutines.db = db
    return db

@pytest.mark.gen_test
def test_update_collection2(set_db):
    db = set_db
    item = {'__client__': None, '__collection__':'A', 'id': '0', 'x': 6}
    client.filters = {}
    client.add_filter('my_filter', {'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 5, 'y': 10, '__key__': [('x', -1), ], '__limit__': 2,
                                    '__skip__': 0})

    to_list = Mock()
    @gen.coroutine
    def f():
        to_list()
        return []

    find_one = Mock()
    @gen.coroutine
    def g(arg):
        find_one(arg)
        return {}

    update = Mock()
    @gen.coroutine
    def h(id, arg):
        update(id, arg)
        return

    db['A'].find_one = g
    db['A'].find().to_list = f
    db['A'].update = h

    yield handle2(item)
    assert find_one.called
    assert to_list.called

# ################################

@pytest.mark.gen_test
def _test_update(set_db):
    db = set_db
    #db = MagicMock()
    #coroutines.db = db
    item = {'__client__': None, '__collection__':'A', 'id': '0', 'x': 6}

    @gen.coroutine
    def f(arg):
        return {'id': '0', 'x': 5}

    update = Mock()
    @gen.coroutine
    def u(id, arg):
        update(id, arg)
        return

    db['A'].find_one = f
    db['A'].update = u

    yield handle(item)
    assert update.called
    assert call({'_id': '0'}, {'$set': {'x': 6}}) in update.mock_calls


@pytest.mark.gen_test
def _test_updateno_pass_validation(set_db):
    db = set_db
    item = {'__client__': None, '__collection__':'A', 'id': '0', 'x': -1}

    @gen.coroutine
    def f(arg):
        return {'id': '0', 'x': 5}

    update = Mock()
    @gen.coroutine
    def u(id, arg):
        update(id, arg)
        return

    db['A'].find_one = f
    db['A'].update = u

    yield handle(item)
    assert not update.called


@pytest.mark.gen_test
def _test_insert(set_db):
    db = set_db
    item = {'__client__': None, '__collection__':'A', 'id': '0', 'x': 6}

    @gen.coroutine
    def f(arg):
        return None

    insert = Mock()
    @gen.coroutine
    def i(arg):
        print('i')
        insert(arg)
        return

    db['A'].find_one = f
    db['A'].insert = i

    yield handle(item)
    assert insert.called
    assert call({'_id': '0', 'x': 6}) in insert.mock_calls


@pytest.mark.gen_test
def _test_insert_no_pass_validation(set_db):
    db = set_db
    item = {'__client__': None, '__collection__':'A', 'id': '0', 'x': -6}

    @gen.coroutine
    def f(arg):
        return None

    insert = Mock()
    @gen.coroutine
    def i(arg):
        insert(arg)
        return

    db['A'].find_one = f
    db['A'].insert = i

    yield handle(item)
    assert not insert.called
