import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
sys.modules['browser'] = Mock()

from components.main.controller import render, makeDIV
from components.main.reactive import Model, consume, execute
from components.main import controller
from collections import namedtuple
from components.lib.filter_mongo import filter, Filter

#filters = {}
#controller.filters = filters
#filters['0'] = lambda x, y: {'__collection__': 'A', 'x': {"$gt": x, "$lt": y}}

@filter('A')
def my_filter(x, y):
    return {'x': {"$gt": x, "$lt": y}}


class A(Model):
    objects = {}

    def hello(self):
        return 'hola'


def test_1():
    consume()
    node1 = MagicMock()
    node1.attr.return_value = 'save'
    node2 = MagicMock()
    node2.attr.return_value = 'save'
    jq = MagicMock()
    node = MagicMock()
    Attribute = namedtuple('Attribute', ['name', 'value'])
    node1[0].attributes = [Attribute('class', '{hello}')]
    node2[0].attributes = []
    node.find().__iter__.return_value = [node1, node2]
    jq.side_effect = [node, node1, node2]

    controller.jq = jq

    model = A(id=None, x=8, y=9)

    node1.outerHTML.return_value = '<span r class="{hello}">{x}</span>'
    node1.html.return_value = '{x}'
    node2.outerHTML.return_value = '<span r>{y}</span>'
    node2.html.return_value = '{y}'

    makeDIV('0', model, render, '<span r class="{hello}">{x}</span> <span r>{y}</span>')

    assert call('8') in node1.html.mock_calls
    assert call('class', 'hola') in node1.attr.mock_calls

    assert call('9') in node2.html.mock_calls
    assert model._dirty == set(['x', 'y'])

    model.x = 800
    #assert len(execute) == 1
    #consume()
    assert call('800') in node1.html.mock_calls


def test_render_model_selection():
    consume()

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

    m = A(id=None, x=8, y=9)

    filter = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 0, 'y': 1000, '__key__': [('x', -1), ], '__limit__': 2,
                                    '__skip__': 0})

    jq.side_effect = [node, node1, node2]
    cc = controller.Controller('cc', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
    jq.side_effect = side_effect
    c = controller.SelectedModelControllerRef('c', cc, selection)

    jq.side_effect = None

    cc.test(m, {'x': 8, 'y': 9, '__skip__': '0'})
    #consume()

    assert not node.html.called
    assert call('8') in node1.html.mock_calls
    assert call('class', '8') in node1.attr.mock_calls
    assert call('9') in node2.html.mock_calls

    m.x = 800
    #assert len(execute) == 1
    #consume()
    assert call('800') in node1.html.mock_calls

    m2 = A(id=None, x=801, y=19)
    cc.test(m2, {'x': 801, 'y': 19, '__skip__': '0'})
    #consume()
    assert c.selected == m2
    assert call('801') in node1.html.mock_calls
    assert call('19') in node2.html.mock_calls
    m2.y = 20
    #assert len(execute) == 1
    #consume()
    assert call('20') in node2.html.mock_calls
    cc.test(m2, {'x': 1001, 'y': 20, '__skip__': '0'})
    #consume()
    assert call('800') in node1.html.mock_calls
    assert c.selected == m
    # falta test de modify


def test_render_model_selection_selected():
    consume()

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

    def selection(lista):
        s = None
        for m_ in lista:
            if m_.selected:
                s = m_
        if s:
            return s
        else:
            return None #A(id=None, x=0, y=0)

    def side_effect(arg):
        if arg == '#cr':
            return node
        if type(arg) is str:
            return node
        return arg

    filter = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 0, 'y': 1000, '__key__': [('x', -1), ], '__limit__': 2,
                                    '__skip__': 0})

    jq.side_effect = [node, node1, node2]
    cc = controller.Controller('cc', key=[('x', 'desc'), ('y', 'desc')], filter=filter)
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
    assert c.selected is None

