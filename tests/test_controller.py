import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
sys.modules['browser'] = Mock()

from components.lib.filter_mongo import Filter, filter
from components.main import controller
from components.main.controller import Controller
from components.main.reactive import Model
from collections import namedtuple
from utils import Node


class DIV(object):
    def __init__(self, Id=None):
        self.id = Id


class A(Model):
    objects = {}

    def __init__(self, id, **kw):
        super(A, self).__init__(id, **kw)

#controller.filters = filters

@filter('A')
def my_filter(x, y):
    return {'x': {"$gt": x, "$lt": y}}


filter = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 5, 'y': 10, '__key__': [('x', 'desc'), ('y', 'desc')], '__limit__': 2,
                                    '__skip__': 0})
m0 = A(id='0', x=0, y=3)
m1 = A(id='1', x=0, y=2)
m = A(id='2', x=0, y=1)


def test_index_in_list_empty(monkeypatch):
    jq = MagicMock()
    monkeypatch.setattr(controller, 'jq', jq)
    c = Controller(name='', filter_=filter)
    c.models = []
    ret = c.indexInList(m)
    assert ret == (0, 'append')


def test_index_in_list_before(monkeypatch):
    jq = MagicMock()
    monkeypatch.setattr(controller, 'jq', jq)
    c = Controller(name='', filter_=filter)
    c.models = [m0]
    m = A(id='2', x=1, y=1)
    ret = c.indexInList(m)
    assert ret == (0, 'before', '0')


def test_index_in_list_before0(monkeypatch):
    jq = MagicMock()
    monkeypatch.setattr(controller, 'jq', jq)
    c = Controller(name='', filter_=filter)
    c.models = [m0]
    m = A(id='2', x=0, y=3)
    ret = c.indexInList(m)
    assert ret == (0, 'before', '0')


def test_index_in_list_after(monkeypatch):
    jq = MagicMock()
    monkeypatch.setattr(controller, 'jq', jq)
    c = Controller(name='', filter_=filter)
    c.models = [m0]
    m = A(id='2', x=-1, y=3)
    ret = c.indexInList(m)
    assert ret == (1, 'after', '0')


def test_index_in_list_second_key_after_2(monkeypatch):
    jq = MagicMock()
    monkeypatch.setattr(controller, 'jq', jq)
    c = Controller(name='', filter_=filter)

    c.models = [m0, m1]
    ret = c.indexInList(m)
    assert ret == (2, 'after', '1')


def test_new_append(monkeypatch):
    jq = MagicMock()
    jq().attr.return_value = False
    jq.find().__iter__.return_value = []
    append = jq().append

    monkeypatch.setattr(controller, 'jq', jq)
    #controller.jq = jq
    controller_ = Controller(name='', filter_=filter)
    m = A(id='2', x=0, y=3)
    controller_.new(m, '0')
    assert append.called
    assert controller_.models == [m]


def test_new_controller_limit_is_0(monkeypatch):
    jq = MagicMock()
    jq.find().__iter__.return_value = []
    append = jq().append
    remove = jq().children().remove
    jq().attr.return_value = False

    #controller.jq = jq
    monkeypatch.setattr(controller, 'jq', jq)
    controller_ = Controller(name='', filter_=filter)
    m = A(id='2', x=0, y=3)
    controller_.limit = 0
    controller_.new(m, '0')
    assert append.called
    assert remove.called
    assert not jq().children().after.called
    assert not jq().children().before.called
    assert controller_.models == []


def test_new__before(monkeypatch):
    jq = MagicMock()
    jq().attr.return_value = False
    jq.find().__iter__.return_value = []
    before = jq().children().before

    #controller.jq = jq
    monkeypatch.setattr(controller, 'jq', jq)
    controller_ = Controller(name='', filter_=filter)
    m = A(id='2', x=0, y=3)
    controller_.models = [m]
    m2 = A(id='3', x=0, y=3)
    controller_.new(m2, 0)

    jq().children.assert_called_with("[reactive_id='2']")
    assert before.called
    assert controller_.models == [m2, m]


def test_new__after(monkeypatch):
    jq = MagicMock()
    jq().attr.return_value = False
    jq.find().__iter__.return_value = []
    after = jq().children().after

    #controller.jq = jq
    monkeypatch.setattr(controller, 'jq', jq)
    controller_ = Controller(name='', filter_=filter)
    m = A(id='2', x=0, y=3)
    controller_.models = [m]
    m2 = A(id='3', x=0, y=2)
    controller_.new(m2, 0)

    jq().children.assert_called_with("[reactive_id='2']")
    assert after.called
    assert controller_.models == [m, m2]


def test_out_not_first(monkeypatch):
    jq = Mock()

    #controller.jq = jq
    monkeypatch.setattr(controller, 'jq', jq)
    controller_ = Controller(name='', filter_=filter)
    m = A(id='2', x=0, y=3)
    controller_.models = [m]

    controller_.out(m)
    assert controller_.models == []


def test_out_not_first_more_than_one(monkeypatch):
    jq = Mock()

    #controller.jq = jq
    monkeypatch.setattr(controller, 'jq', jq)
    controller_ = Controller(name='', filter_=filter)
    m = A(id='2', x=0, y=3)
    m2 = A(id='3', x=0, y=3)
    controller_.models = [m, m2]

    controller_.out(m)
    assert controller_.models == [m2]


def test_modify_when_move_to__after(monkeypatch):
    jq = Mock()
    children = jq().children

    #controller.jq = jq
    monkeypatch.setattr(controller, 'jq', jq)
    controller_ = Controller(name='', filter_=filter)
    m = A(id='2', x=0, y=3)
    m2 = A(id='3', x=0, y=2)
    controller_.models = [m, m2]
    m.y = 1

    controller_.modify(m)

    assert call("[reactive_id='2']") == children.mock_calls[0]

    assert call("[reactive_id='3']") == children.mock_calls[1]
    assert children().after.called
    assert controller_.models == [m2, m]


def test_modify_when_move_to__before(monkeypatch):
    jq = Mock()
    children = jq().children

    #controller.jq = jq
    monkeypatch.setattr(controller, 'jq', jq)
    controller_ = Controller(name='', filter_=filter)
    m = A(id='2', x=0, y=3)
    m2 = A(id='3', x=0, y=2)
    controller_.models = [m, m2]
    m2.y = 4

    controller_.modify(m2)

    assert call("[reactive_id='3']") == children.mock_calls[0]

    assert call("[reactive_id='2']") == children.mock_calls[1]
    assert children().before.called
    assert controller_.models == [m2, m]

# ####################


def test_SelectedModelControllerRef(monkeypatch):

    node = Node("<div id='c'><span template=true class='template'><span class='{x} hola' r>{x}</span><span r>{y}</span></span></div>")
    node2 = Node("<div id='cr'><span class='template' template=true><span class='{x} hola' r>{x}</span><span r>{y}</span></span>")

    def jq(arg):
        print('side effect', arg)
        if arg == '#c':
            return node
        if arg == '#cr':
            return node2
        if arg == '#c .template':
            return node.first()
        if type(arg) == str:
            return Node(arg)
        print('retorno', arg)
        return arg

    monkeypatch.setattr(controller, 'jq', jq)

    m = A(id=None, x=8, y=9)
    m_empty = A(id=None, x='', y='')
    filter = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 0, 'y': 1000, '__key__': [('x', 'desc'), ('y', 'desc')], '__limit__': 2,
                                    '__skip__': 0})

    c = controller.Controller('c', filter_=filter)

    def selection(lista):
        s = m_empty
        for m_ in lista:
            if m_.selected:
                s = m_
        return s

    cr = controller.SelectedModelControllerRef('cr', c, selection)

    c.test(m, {'x': 8, 'y': 9, '__skip__': '0'})
    assert cr.selected is m_empty
    m.selected = True
    assert cr.selected == m

    m2 = A(id=None, x=801, y=19)
    c.test(m2, {'x': 801, 'y': 19, '__skip__': '0'})
    m.selected = False
    m2.selected = True

    assert cr.selected == m2

    m3 = A(id=None, x=1, y=1)
    c.test(m3, {'x': 1, 'y': 1, '__skip__': '0'})
    m2.selected = False
    m3.selected = True

    assert cr.selected == m3
    m3.x = -1
    c.test(m3, {'x': -1, 'y': 1, '__skip__': '0'})
    assert cr.selected is m_empty


def test_render_model_selection_selected(monkeypatch):
    node = Node("<div id='cc'><span template=true class='template'><span class='{x} hola' r>{x}</span><span r>{y}</span></span></div>")
    node2 = Node("<div id='c'><span class='template' template=true><span class='{x} hola' r>{x}</span><span r>{y}</span></span>")

    def jq(arg):
        print('side effect', arg)
        if arg == '#cc':
            return node
        if arg == '#c':
            return node2
        if arg == '#cc .template':
            return node.first()
        if type(arg) == str:
            return Node(arg)

        return arg

    monkeypatch.setattr(controller, 'jq', jq)

    m_empty = A(id=None, x='', y='')
    def selection(lista):
        s = None
        for m_ in lista:
            if m_.selected:
                s = m_
        if s:
            return s
        else:
            return m_empty

    def side_effect(arg):
        if arg == '#cr':
            return node
        if type(arg) is str:
            return node
        return arg

    filter = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 0, 'y': 1000, '__key__': [('x', 'desc'), ('y', 'desc')], '__limit__': 2,
                                    '__skip__': 0})

    cc = controller.Controller('cc', filter_=filter)
    jq.side_effect = side_effect
    c = controller.SelectedModelControllerRef('c', cc, selection_func=selection)

    m = A(id=None, x=8, y=9)

    cc.test(m, {'x': 8, 'y': 9, '__skip__': '0'})
    #consume()

    m.selected = True
    #consume()

    assert c.selected == m

    m2 = A(id=None, x=801, y=19)
    cc.test(m2, {'x': 801, 'y': 19, '__skip__': '0'})
    m.selected = False
    m2.selected = True
    #consume()
    assert c.selected == m2

    m3 = A(id=None, x=1, y=1)
    cc.test(m3, {'x': 1, 'y': 1, '__skip__': '0'})
    m2.selected = False
    m3.selected = True
    #consume()
    assert c.selected == m3
    m3.x = -1
    cc.test(m3, {'x': -1, 'y': 1, '__skip__': '0'})
    assert c.selected is m_empty


def test_render_model_selection(monkeypatch):
    node = Node("<div id='cc'><span class='template'><span class='{x} hola' r>{x}</span><span r>{y}</span></span></div>")
    node2 = Node("<div id='c'><span class='template'><span class='{x} hola' r>{x}</span><span r>{y}</span></span>")

    def jq(arg):
        print('side effect', arg)
        if arg == '#cc':
            return node
        if arg == '#c':
            return node2
        if arg == '#cc .template':
            return node.first()
        if type(arg) == str:
            return Node(arg)

        return arg

    monkeypatch.setattr(controller, 'jq', jq)

    def selection(lista):
        if len(lista) > 0:
            return lista[0]
        else:
            return A(id=None, x=0, y=0)

    def side_effect(arg):
        if arg == '#cr':
            return node
        if type(arg) is str:
            return node
        return arg

    m = A(id='0', x=8, y=9)

    filter = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 0, 'y': 1000, '__key__': [('x', 'desc'), ('y', 'desc')], '__limit__': 1,
                                    '__skip__': 0})

    cc = controller.Controller('cc', filter_=filter)
    c = controller.SelectedModelControllerRef('c', cc, selection)

    cc.test(m, {'x': 8, 'y': 9, '__skip__': '0'})

    assert node2.children().first().children().first().html() == '8'
    assert node2.children().first().children().first().outerHTML == '<span class="8 hola" r="">8</span>'

    m.x = 800
    assert node2.children().first().children().first().outerHTML == '<span class="800 hola" r="">800</span>'

    m2 = A(id='2', x=801, y=19)
    cc.test(m2, {'x': 801, 'y': 19, '__skip__': '2'})
    assert c.selected == m2
    assert node2.children().first().children().first().outerHTML == '<span class="801 hola" r="">801</span>'

    m2.y = 20
    assert node2.children().first().children()[-1].outerHTML == '<span r="">20</span>'

    cc.test(m, {'x': 800, 'y': 20, '__skip__': '0'})
    assert len(cc.models) == 1
    assert c.selected == m
    assert node2.children().first().children().first().outerHTML == '<span class="800 hola" r="">800</span>'
