import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
sys.modules['browser'] = Mock()

from components.main.controller import render_ex, format_attr, render
from bs4 import BeautifulSoup
from components.main.reactive import Model
from components.main import controller
from utils import Node

#helpers = {}

def side_effect(arg):
    return arg
jq = MagicMock()
jq.side_effect = side_effect
controller.jq = jq



class A(Model):
    objects = {}

    def __init__(self, id, **kw):
        super(A, self).__init__(id, **kw)

    def h(self):
        return self.x > 10

    def xplus1(self):
        return self.x + 1

    def k(self):
        return 'hello'


class Controller(object):
    def foo(self, model):
        return 'world'


class Attribute(object):
    def __init__(self, name):
        self.name = name

    @staticmethod
    def make_attributes(lista):
        ret = []
        for item in lista:
            ret.append(Attribute(item))
        return ret


def test_format_attr():
    m = A(id=None, x=8, y=9, z=False)
    dct = {'attr1': '{k}', 'class': 'hola {k} mundo', 'foo': '{foo}'}
    assert format_attr(m, dct, Controller()) == {'class': 'hola hello mundo', 'attr1': 'hello', 'foo': 'world'}


def test_render():
    m = A(id=None, x=8, y=9, z=False)
    n = MagicMock()
    n.attr.return_value = False

    n[0].attributes = Attribute.make_attributes(['class', 'value-integer'])
    c = None
    template = "<span r class='{k} world'>{x}</span>"
    attributes = {'class': '{k} world', 'value-integer': '{x}'}

    render(n, m, c, template, attributes)
    assert call("<span r class='hello world'>8</span>") in n.html.mock_calls
    print(n.attr.mock_calls)
    assert call('class', 'hello world') in n.attr.mock_calls
    assert n.val.called



def test_basic_render_ex():
    node = Node("<div if='{z}'><span id='0' class='template'><span r>{x}</span><span r>{y}</span></span></div>")
    m = A(id=None, x=8, y=9, z=False)
    render_ex(node, m)
    assert node.children() == []
    m.y = 900
    assert node.children() == []
    m.y = 901
    assert node.children() == []
    m.z = True
    assert len(node.children()) == 1
    assert node.children()[0].attr('id') == '0'

    assert node.children().first().children().first().html() == '8' #  '<span r="">8</span>'
    assert node.children().first().children()[-1].html() == '901' # '<span r="">901</span>'
    assert m._dirty == set(['x', 'y', 'z'])
    m.z = False
    assert node.children() == []
    m.x = 1000
    assert node.children() == []
    m.z = True
    assert len(node.children()) == 1
    assert node.children()[0].attr('id') == '0'


def test_basic_render_ex_method():
    node = Node("<div if='{h}'><span id='0' class='template'><span r on-click='{xplus1}'>{x}</span><span r>{y}</span></span></div>")
    m = A(id=None, x=8, y=9, z=False)
    render_ex(node, m)
    assert node.children() == []
    m.y = 900
    assert node.children() == []
    m.x = 9
    assert node.children() == []
    m.x = 11
    assert len(node.children()) == 1
    assert node.children().first().children().first().click() == 12
    assert node.children()[0].attr('id') == '0'

    m.x = 12
    assert len(node.children()) == 1
    assert len(node.children().first().children()) == 2

    m.x = 0
    assert len(node.children()) == 0

