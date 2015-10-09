import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
sys.modules['browser'] = Mock()

import pytest
from tornado import gen

from server.main.coroutines import broadcast_helper as broadcast
from  server.main import coroutines

@pytest.mark.gen_test
def test_circuit_0():
    skip = 1
    limit = 2
    total_before = ['1']
    total_after = ['0', '1']
    x = yield broadcast({'id': '0'}, total_before, total_after, limit, skip)

    assert x == {'id': '0', '__new__': True, '__position__': ('before', 0)}

@pytest.mark.gen_test
def test_circuit_0a():
    skip = 1
    limit = 1
    total_before = ['1']
    total_after = ['0']
    x = yield broadcast({'id': '0'}, total_before, total_after, limit, skip)

    assert x == {'id': '0', '__out__': '1', '__new__': True, '__position__': ('append', 0)}

@pytest.mark.gen_test
def test_circuit_1(monkeypatch):
    @gen.coroutine
    def f(*args, **kwargs):
        return {'id': '1'}

    monkeypatch.setattr(coroutines, 'do_find_one', f)

    skip = 1
    limit = 1
    total_before = ['0']
    total_after = ['1']
    x = yield broadcast({'id': '0'}, total_before, total_after, limit, skip)

    assert x == {'id': '1', '__out__': '0', '__new__': True, '__position__': ('append', 0)}


@pytest.mark.gen_test
def test_circuit_1a(monkeypatch):
    @gen.coroutine
    def f(*args, **kwargs):
        return {'id': '1'}

    monkeypatch.setattr(coroutines, 'do_find_one', f)

    skip = 1
    limit = 1
    total_before = ['2']
    total_after = ['1']
    x = yield broadcast({'id': '0'}, total_before, total_after, limit, skip)

    assert x == {'id': '1', '__new__': True, '__position__': ('append', 0)}


@pytest.mark.gen_test
def test_circuit_2(monkeypatch):
    @gen.coroutine
    def f(*args, **kwargs):
        return {'id': '1'}

    monkeypatch.setattr(coroutines, 'do_find_one', f)

    skip = 1
    limit = 1
    total_before = ['0', '1', '2']
    total_after = ['0', '2']
    x = yield broadcast({'id': '1'}, total_before, total_after, limit, skip)

    assert x == {'id': '1', '__out__': '1'}

# ################

@pytest.mark.gen_test
def test_empties():
    skip = 1
    limit = 1
    total_before = []
    total_after = []
    x = yield broadcast({'id': '0'}, [], [], limit, skip)

    assert x is None

@pytest.mark.gen_test
def test_modify():
    skip = 0
    limit = 1
    before = ['0']
    after = ['0']
    x = yield broadcast({'id': '0'}, before, after, limit, skip)

    assert x == {'id': '0', '__position__': ('append', 0)}

@pytest.mark.gen_test
def test_new():
    skip = 0
    limit = 1
    before = []
    after = ['0']
    x = yield broadcast({'id': '0'}, before, after, limit, skip)

    assert x == {'id': '0', '__new__': True, '__position__': ('append', 0)}

@pytest.mark.gen_test
def test_simple_out():
    x = yield  broadcast({'id': '0'}, ['0'], [], 1, 0)
    assert x == {'id': '0', '__out__': '0'}

@pytest.mark.gen_test
def test_new_but_no_success():
    skip = 0
    limit = 1
    before = ['1']
    after = ['1']
    x = yield broadcast({'id': '0'}, before, after, limit, skip)

    assert x is None

@pytest.mark.gen_test
def test_new_out_previous():
    skip = 0
    limit = 1
    before = ['1']
    after = ['0']
    x = yield broadcast({'id': '0'}, before, after, limit, skip)

    assert x == {'id': '0', '__new__': True, '__out__': '1', '__position__': ('append', 0)}

@pytest.mark.gen_test
def test_basic(monkeypatch):

    @gen.coroutine
    def f(*args, **kwargs):
        return {'id': '1'}

    monkeypatch.setattr(coroutines, 'do_find_one', f)
    skip = 1
    limit = 1
    total_before = ['-1', '0', '1']
    total_after = ['-1', '1', '0']
    x = yield broadcast({'id': '0'}, total_before[skip: skip+limit], total_after[skip: skip+limit], limit, skip)

    assert x == {'id': '1', '__out__': '0', '__new__': True, '__position__': ('append', 0)}

@pytest.mark.gen_test
def test_basic2(monkeypatch):

    @gen.coroutine
    def f(*args, **kwargs):
        return {'id': '9'}

    monkeypatch.setattr(coroutines, 'do_find_one', f)

    skip = 0
    limit = 2
    tbefore = ['-1', '0', '9']
    tafter = ['-1', '9', '0']
    x = yield broadcast({'id': '0'}, tbefore[skip: skip+limit], tafter[skip: skip+limit], limit, skip)

    assert x == {'id': '9', '__out__': '0', '__new__': True, '__position__': ('-1', 1)}

