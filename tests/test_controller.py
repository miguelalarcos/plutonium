import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
sys.modules['browser'] = Mock()

from components.main import controller
from components.main.controller import Controller
from components.main.reactive import Model
from collections import namedtuple


class DIV(object):
    def __init__(self, Id=None):
        self.id = Id


class A(Model):
    objects = {}

    def __init__(self, id, **kw):
        super(A, self).__init__(id, **kw)

filters = {}
controller.filters = filters
filters['0'] = lambda x, y: {'__collection__': 'A', 'x': {"$gt": x, "$lt": y}}

#filter = filters['0'](x=5, y=10)
filter = ('0', {'x': 5, 'y': 10})
m0 = A(id='0', x=0, y=3)
m1 = A(id='1', x=0, y=2)
m = A(id='2', x=0, y=1)


def test_index_in_list_empty():
    controller = Controller(name='', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
    controller.models = []
    ret = controller.indexInList(m)
    assert ret == (0, 'append')


def test_index_in_list_before():
    controller = Controller(name='', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
    controller.models = [m0]
    m = A(id='2', x=1, y=1)
    ret = controller.indexInList(m)
    assert ret == (0, 'before', '0')


def test_index_in_list_before0():
    controller = Controller(name='', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
    controller.models = [m0]
    m = A(id='2', x=0, y=3)
    ret = controller.indexInList(m)
    assert ret == (0, 'before', '0')


def test_index_in_list_after():
    controller = Controller(name='', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
    controller.models = [m0]
    m = A(id='2', x=-1, y=3)
    ret = controller.indexInList(m)
    assert ret == (1, 'after', '0')


def test_index_in_list_second_key_after_2():
    controller = Controller(name='', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
    controller.models = [m0, m1]
    ret = controller.indexInList(m)
    assert ret == (2, 'after', '1')


def test_new_append():
    jq = MagicMock()
    jq.find().__iter__.return_value = []
    append = jq().append

    controller.jq = jq
    controller_ = Controller(name='', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
    m = A(id='2', x=0, y=3)
    controller_.new(m)
    assert append.called
    assert controller_.models == [m]


def test_new__before():
    jq = MagicMock()
    jq.find().__iter__.return_value = []
    before = jq().children().before

    controller.jq = jq
    controller_ = Controller(name='', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
    m = A(id='2', x=0, y=3)
    controller_.models = [m]
    m2 = A(id='3', x=0, y=3)
    controller_.new(m2)

    jq().children.assert_called_with("[reactive_id='2']")
    assert before.called
    assert controller_.models == [m2, m]


def test_new__after():
    jq = MagicMock()
    jq.find().__iter__.return_value = []
    after = jq().children().after

    controller.jq = jq
    controller_ = Controller(name='', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
    m = A(id='2', x=0, y=3)
    controller_.models = [m]
    m2 = A(id='3', x=0, y=2)
    controller_.new(m2)

    jq().children.assert_called_with("[reactive_id='2']")
    assert after.called
    assert controller_.models == [m, m2]


def test_out_not_first():
    jq = Mock()

    controller.jq = jq
    controller_ = Controller(name='', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
    m = A(id='2', x=0, y=3)
    controller_.models = [m]

    controller_.out(m)
    assert controller_.models == []


def test_out_not_first_more_than_one():
    jq = Mock()

    controller.jq = jq
    controller_ = Controller(name='', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
    m = A(id='2', x=0, y=3)
    m2 = A(id='3', x=0, y=3)
    controller_.models = [m, m2]

    controller_.out(m)
    assert controller_.models == [m2]


def test_modify_when_move_to__after():
    jq = Mock()
    children = jq().children

    controller.jq = jq
    controller_ = Controller(name='', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
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


def test_modify_when_move_to__before():
    jq = Mock()
    children = jq().children

    controller.jq = jq
    controller_ = Controller(name='', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
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


def test_SelectedModelControllerRef():
    node = MagicMock()
    node1 = MagicMock()
    Attribute = namedtuple('Attribute', ['name', 'value'])
    node1[0].attributes = [Attribute('class', '{x}')]
    node2 = MagicMock()
    node2[0].attributes = []
    jq = MagicMock()
    controller.jq = jq

    node.find().__iter__.return_value = [node1, node2]
    node1.outerHTML.return_value = '<span r class="{x}">{x}</span>'
    node1.html.return_value = '{x}'
    node2.outerHTML.return_value = '<span r>{y}</span>'
    node2.html.return_value = '{y}'

    def side_effect(arg):
        if type(arg) is Mock:
            return arg
        if type(arg) is str:
            return node
        return arg


    m = A(id=None, x=8, y=9)
    jq.side_effect = side_effect
    c = controller.Controller('c', key=[('x', 'desc'), ('y', 'desc')], filter=('0', {'x': 0, 'y': 1000}))
    cr = controller.SelectedModelControllerRef('cr', c)

    c.test(m, {'x': 8, 'y': 9})
    assert cr.selected is None
    m.selected = True
    assert cr.selected == m

    m2 = A(id=None, x=801, y=19)
    c.test(m2, {'x': 801, 'y': 19})
    m.selected = False
    m2.selected = True

    assert cr.selected == m2

    m3 = A(id=None, x=1, y=1)
    c.test(m3, {'x': 1, 'y': 1})
    m2.selected = False
    m3.selected = True

    assert cr.selected == m3
    m3.x = -1
    c.test(m3, {'x': -1, 'y': 1})
    assert cr.selected is None

