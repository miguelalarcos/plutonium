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


def test_index_in_list_empty():
    controller = Controller(name='', filter=filter)
    controller.models = []
    ret = controller.indexInList(m)
    assert ret == (0, 'append')


def test_index_in_list_before():
    controller = Controller(name='', filter=filter)
    controller.models = [m0]
    m = A(id='2', x=1, y=1)
    ret = controller.indexInList(m)
    assert ret == (0, 'before', '0')


def test_index_in_list_before0():
    controller = Controller(name='', filter=filter)
    controller.models = [m0]
    m = A(id='2', x=0, y=3)
    ret = controller.indexInList(m)
    assert ret == (0, 'before', '0')


def test_index_in_list_after():
    controller = Controller(name='', filter=filter)
    controller.models = [m0]
    m = A(id='2', x=-1, y=3)
    ret = controller.indexInList(m)
    assert ret == (1, 'after', '0')


def test_index_in_list_second_key_after_2():
    controller = Controller(name='', filter=filter)
    controller.models = [m0, m1]
    ret = controller.indexInList(m)
    assert ret == (2, 'after', '1')


def test_new_append(monkeypatch):
    jq = MagicMock()
    jq().attr.return_value = False
    print('nodo principal', jq())
    jq.find().__iter__.return_value = []
    append = jq().append

    monkeypatch.setattr(controller, 'jq', jq)
    #controller.jq = jq
    controller_ = Controller(name='', filter=filter)
    m = A(id='2', x=0, y=3)
    controller_.new(m, '0')
    assert append.called
    assert controller_.models == [m]


def test_new_controller_limit_is_0(monkeypatch):
    jq = MagicMock()
    jq.find().__iter__.return_value = []
    append = jq().append
    remove = jq().children().remove

    #controller.jq = jq
    monkeypatch.setattr(controller, 'jq', jq)
    controller_ = Controller(name='', filter=filter)
    m = A(id='2', x=0, y=3)
    controller_.limit = 0
    controller_.new(m, '0')
    assert not append.called
    assert not remove.called
    assert not jq().children().after.called
    assert not jq().children().before.called
    assert controller_.models == []


def _test_new__before(monkeypatch):
    jq = MagicMock()
    jq.find().__iter__.return_value = []
    before = jq().children().before

    #controller.jq = jq
    monkeypatch.setattr(controller, 'jq', jq)
    controller_ = Controller(name='', filter=filter)
    m = A(id='2', x=0, y=3)
    controller_.models = [m]
    m2 = A(id='3', x=0, y=3)
    controller_.new(m2, 0)

    jq().children.assert_called_with("[reactive_id='2']")
    assert before.called
    assert controller_.models == [m2, m]


def _test_new__after(monkeypatch):
    jq = MagicMock()
    jq.find().__iter__.return_value = []
    after = jq().children().after

    #controller.jq = jq
    monkeypatch.setattr(controller, 'jq', jq)
    controller_ = Controller(name='', filter=filter)
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
    controller_ = Controller(name='', filter=filter)
    m = A(id='2', x=0, y=3)
    controller_.models = [m]

    controller_.out(m)
    assert controller_.models == []


def test_out_not_first_more_than_one(monkeypatch):
    jq = Mock()

    #controller.jq = jq
    monkeypatch.setattr(controller, 'jq', jq)
    controller_ = Controller(name='', filter=filter)
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
    controller_ = Controller(name='', filter=filter)
    m = A(id='2', x=0, y=3)
    m2 = A(id='3', x=0, y=2)
    controller_.models = [m, m2]
    m.y = 1

    controller_.modify(m)

    assert call("[reactive_id='2']") == children.mock_calls[0]
    assert children().remove.called
    assert call("[reactive_id='3']") == children.mock_calls[2]
    assert children().after.called
    assert controller_.models == [m2, m]


def test_modify_when_move_to__before(monkeypatch):
    jq = Mock()
    children = jq().children

    #controller.jq = jq
    monkeypatch.setattr(controller, 'jq', jq)
    controller_ = Controller(name='', filter=filter)
    m = A(id='2', x=0, y=3)
    m2 = A(id='3', x=0, y=2)
    controller_.models = [m, m2]
    m2.y = 4

    controller_.modify(m2)

    assert call("[reactive_id='3']") == children.mock_calls[0]
    assert children().remove.called
    assert call("[reactive_id='2']") == children.mock_calls[2]
    assert children().before.called
    assert controller_.models == [m2, m]

# ####################


def test_SelectedModelControllerRef(monkeypatch):
    #node = MagicMock()
    #node1 = MagicMock()
    #Attribute = namedtuple('Attribute', ['name', 'value'])
    #node1[0].attributes = [Attribute('class', '{x}')]
    #node2 = MagicMock()
    #node2[0].attributes = []
    #jq = MagicMock()
    #controller.jq = jq

    #node.find().__iter__.return_value = [node1, node2]
    #node1.outerHTML.return_value = '<span r class="{x}">{x}</span>'
    #node1.html.return_value = '{x}'
    #node2.outerHTML.return_value = '<span r>{y}</span>'
    #node2.html.return_value = '{y}'

    #def side_effect(arg):
    #    return arg
    #jq = MagicMock()




    node = Node("<div id='c'><span template=true class='template'><span class='{x} hola' r>{x}</span><span r>{y}</span></span></div>")
    node2 = Node("<div id='cr'><span class='template' template=true><span class='{x} hola' r>{x}</span><span r>{y}</span></span>")

    def jq(arg):
        print('side effect', arg)
        if arg == '#c':
            return node
        if arg == '#cr':
            return node2
        if arg == '#c .template':
            return node.first() #Node("<span template=true class='template'><span class='{x} hola' r>{x}</span><span r>{y}</span></span>")
        if type(arg) == str:
            return Node(arg)
        print('retorno', arg)
        return arg
    #jq.side_effect = side_effect
    #controller.jq = jq
    monkeypatch.setattr(controller, 'jq', jq)

    m = A(id=None, x=8, y=9)
    #jq.side_effect = side_effect

    filter = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 0, 'y': 1000, '__key__': [('x', 'desc'), ('y', 'desc')], '__limit__': 2,
                                    '__skip__': 0})

    c = controller.Controller('c', filter=filter)
    cr = controller.SelectedModelControllerRef('cr', c)

    c.test(m, {'x': 8, 'y': 9, '__skip__': '0'})
    assert cr.selected is None
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
    assert cr.selected is None

