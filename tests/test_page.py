import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
browser_mock = Mock()
sys.modules['browser'] = browser_mock

#import browser
#window = browser.window
#jq = window.jq

from components.main.reactive import Model, reactive
from components.main.page import Query, Controller, parse
import components.main.page
from pyquery import PyQuery


class ExtendedPyQuery(PyQuery):
    _data = {}
    _click = {}
    _keyup = {}

    def keyup(self, method=None):
        if method:
            ExtendedPyQuery._keyup[self.attr('id')] = method
        else:
            ExtendedPyQuery._keyup[self.attr('id')]()

    def click(self, method=None):
        if method:
            ExtendedPyQuery._click[self.attr('id')] = method
        else:
            ExtendedPyQuery._click[self.attr('id')]()

    def data(self, key, data=None):
        if data is None:
            return ExtendedPyQuery._data.get(self.attr('id'))
        ExtendedPyQuery._data[self.attr('id')] = data

    @staticmethod
    def contains(document, node):
        node = jq(node)
        id_ = node.attr('id') or 'None'
        if len(document.find('#'+id_)):
            return True
        rid = node.attr('reactive_id') or 'None'
        if len(document.find("[reactive_id='" + rid + "']")):
            return True
        return False

jq = ExtendedPyQuery
components.main.page.jq = jq
#document = None


class MyQuery(Query):
    _collection = 'A'

    def query(self):
        return {'x': {'$gte': self.a, '$lte': self.b}}


class MyController(Controller):
    def __init__(self, id, *args, **kwargs):
        super().__init__(id, *args, **kwargs)
        self.ws = Mock()
        @reactive
        def f():
            q = MyQuery(id='0', sort=(('x', 1),), skip=0, limit=1, a=self.a, b=self.b)
            self.subscribe(q)

    def x(self):
        return False


class A(Model):
    objects = {}

    def h(self):
        return self.z != 9

    def hello(self):
        return 'hello world!' + self.post

    def click(self):
        print('click')


def test_0():
    node = jq("<div class='page'><div id='a' if={x}><div id='t1' class='template'><div r id='0'>{y}</div><div r id='1'>{z}</div></div></div></div>")

    components.main.page.document = node
    parse(MyController(id=None, a=0, b=10), node)
    assert str(node) == '<div class="page"><div id="a" if="{x}"/></div>'


def test_if_if():
    node = jq('<div class="page"><div id="a" if="{a}"><div id="b" if="{b}"><div id="0" class="template">hola{hhh}</div></div></div></div>')
    global document
    document = node
    c = Controller(id=None, a=True, b=True)
    parse(c, node)
    assert str(node) == '<div class="page"><div id="a" if="{a}"><div id="b" if="{b}"><div id="0" class="template">hola{hhh}</div></div></div></div>'
    c.a = False
    assert str(node) == '<div class="page"><div id="a" if="{a}"/></div>'
    c.b = False
    assert str(node) == '<div class="page"><div id="a" if="{a}"/></div>'
    c.b = True
    assert str(node) == '<div class="page"><div id="a" if="{a}"/></div>'
    c.a = True
    assert str(node) == '<div class="page"><div id="a" if="{a}"><div id="b" if="{b}"><div id="0" class="template">hola{hhh}</div></div></div></div>'


def test_class_and_if_model():
    a = A(id=None, y=8, z=9, post='')
    node = jq("<div id='a' class='container'><div r id='0' class={hello}>{y}</div><div id='b' if={h}><div r id='1'>{z}</div></div></div>")
    components.main.page.document = node
    parse(a, node)

    a.z = 11
    assert str(node) == '<div id="a" class="container"><div r="" id="0" class="hello world!">8</div><div id="b" if="{h}"><div r="" id="1">11</div></div></div>'
    print('a.z=9')
    a.z = 9
    assert str(node) == '<div id="a" class="container"><div r="" id="0" class="hello world!">8</div><div id="b" if="{h}"></div></div>'
    print('a.z=13')
    a.z = 13
    assert str(node) == '<div id="a" class="container"><div r="" id="0" class="hello world!">8</div><div id="b" if="{h}"><div r="" id="1">13</div></div></div>'
    print('a.post x')
    a.post = 'x'
    assert str(node) == '<div id="a" class="container"><div r="" id="0" class="hello world!x">8</div><div id="b" if="{h}"><div r="" id="1">13</div></div></div>'


def test_on_click():
    a = A(id=None, y=8)
    node = jq("<div class='container'><div r id='0' on-click={click}>{y}</div></div>")
    components.main.page.document = node
    parse(a, node)

    n = node.find('#0')
    n.click()


def test_integer_value():
    a = A(id=None, y=8)
    node = jq("<div id='a' class='container'><input r id='0' integer-value={y}></div>")
    components.main.page.document = node
    parse(a, node)

    n = node.find('#0')
    assert n.val() == '8'
    n.val('10')
    n.keyup()
    assert a.y == 10


def test_register():
    node = jq('<div class="page"><div id="0" query-id="0" class="container"><span r>{x}</span></div></div>')
    components.main.page.document = node

    c = MyController(id=None, a=0, b=10)

    parse(c, node)

    c.a = 1

    a = A(id='000', x=-1)
    a2 = A(id='111', x= 800)
    c.test(a, {'__position__': 'append', 'x': 1, '__new__': True, '__query__': "('MyQuery', (('__collection__', 'A'), ('__limit__', 1), ('__skip__', 0), ('__sort__', (('x', 1),)), ('a', 1), ('b', 10)))"})
    print('->', node)
    c.test(a, {'x':0, '__out__': '000',  '__query__': "('MyQuery', (('__collection__', 'A'), ('__limit__', 1), ('__skip__', 0), ('__sort__', (('x', 1),)), ('a', 1), ('b', 10)))"})
    print('->', node)

    c.test(a, {'__position__': 'append', 'x': 1, '__new__': True, '__query__': "('MyQuery', (('__collection__', 'A'), ('__limit__', 1), ('__skip__', 0), ('__sort__', (('x', 1),)), ('a', 1), ('b', 10)))"})
    c.test(a2, {'__position__': 'append', 'x':0, '__new__': True, '__skip__': '111', '__query__': "('MyQuery', (('__collection__', 'A'), ('__limit__', 1), ('__skip__', 0), ('__sort__', (('x', 1),)), ('a', 1), ('b', 10)))"})
    print('->', node)
