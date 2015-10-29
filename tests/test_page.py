import sys
import datetime

sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
browser_mock = Mock()
sys.modules['browser'] = browser_mock

from lxml.html import InputElement


from components.main.reactive import Model, reactive
from components.main.page import parse, PageController
from components.main.query import Query
import components.main.page
from pyquery import PyQuery


class ExtendedPyQuery(PyQuery):
    _data = {}
    _click = {}
    _keyup = {}

    def keyup(self, method=None, event=None):
        if method:
            ExtendedPyQuery._keyup[self.attr('id')] = method
        else:
            ExtendedPyQuery._keyup[self.attr('id')](event)

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

    def unbind(self):
        pass

jq = ExtendedPyQuery
components.main.page.jq = jq
#document = None


class MyQuery(Query):
    _collection = 'A'
    reactives = ['selected']

    def query(self):
        return {'x': {'$gte': self.a, '$lte': self.b}}


class MyController(PageController):
    reactives = ['a', 'b']
    ws = Mock()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        @reactive
        def f():
            self.q = self.subscribe(id='0', klass=MyQuery, name='', sort=(('x', 1),), skip=0, limit=1, a=self.a, b=self.b)
            a = A(y=0, z=9)
            self.q.models = [a]
            self.q.selected = a

            self.q2 = self.subscribe(id='1', klass=MyQuery, name='', sort=(('x', 1),), skip=0, limit=1, a=self.a, b=self.b)
            b = B(x=0, y=0)
            self.q2.models = [b]
            self.q2.selected = b

    def x(self):
        return False


class B(Model):
    objects = {}
    reactives = ['x', 'y']

    def f(self, q1, ma, q0, c):
        print('>>>', self, q1, ma, q0, c)
        if self is q1.selected and ma is q0.selected:
            return 'Eureka!!!'
        else:
            return 'None'


class A(Model):
    objects = {}
    reactives = ['y', 'z', 'flag', 'post']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        @reactive
        def r():
            self.flag = self.h()

    def h(self):
        return self.z != 9

    def hello(self, *args):
        return 'hello world!' + self.post

    def click(self, q):
        print('click')

    def f(self, *args):
        print('>>>', *args)
        return 'f'

class EventKeyUp:
    def __init__(self, which):
        self.which = which

def test_attr():
    InputElement.setSelectionRange = Mock()
    InputElement.selectionStart = 0

    a = A(id=None, y=0, z=9)
    node = jq("<div id='a'><input r id='0' attr='y integer_getter integer_setter'></div>")
    components.main.page.document = node
    class MyQuery(Query):
        reactives = []
    q = MyQuery('', '', None, 0, 1)

    parse(node, a, q)

    n = node.find('#0')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '0'
    n.val('10')
    n.keyup(event=EventKeyUp(44))
    assert call(1, 1) in InputElement.setSelectionRange.mock_calls
    n.val('1000')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '1,000'
    assert a.y == 1000

def test_attr_phone():
    InputElement.setSelectionRange = Mock()
    InputElement.selectionStart = 0

    a = A(id=None, y='659688973', z=9)
    node = jq("<div id='a'><input r id='0' attr='y phone_getter phone_setter'></div>")
    components.main.page.document = node
    class MyQuery(Query):
        reactives = []
    q = MyQuery('', '', None, 0, 1)

    parse(node, a, q)

    n = node.find('#0')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '(659)-68 89 73'

    n.val('12')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '12'

    n.val('123')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '(123)-'

    n.val('(123)-')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '(123)-'

    n.val('(123)-4')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '(123)-4'

    n.val('12345')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '(123)-45'

    n.val('(123)-45')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '(123)-45'

    n.val('123456')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '(123)-45 6'

def test_attr_datetime():
    InputElement.setSelectionRange = Mock()
    InputElement.selectionStart = 0

    a = A(id=None, y=datetime.datetime(2015,12,31), z=9)
    node = jq("<div id='a'><input r id='0' attr='y datetime_getter datetime_setter'></div>")
    components.main.page.document = node
    class MyQuery(Query):
        reactives = []
    q = MyQuery('', '', None, 0, 1)

    parse(node, a, q)

    n = node.find('#0')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '31-12-2015'
    n.val('31')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '31'
    n.val('31-12')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '31-12'
    assert a.y == '31-12'

    n.val('3112')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '3112'
    assert a.y == '3112'

    n.val('31122015')
    n.keyup(event=EventKeyUp(44))
    assert n.val() == '31-12-2015'

    assert a.y == datetime.datetime(2015, 12, 31)

def test_if_if():
    node = jq('<div class="page"><div id="a" if="a"><div id="b" if="b"><div id="0" each="0">hola{hhh}</div></div></div></div>')
    global document
    document = node
    components.main.page.document = node
    c = MyController(a=True, b=True)
    parse(node, c)
    assert str(node) == '<div class="page"><div id="a" if="a"><div id="b" if="b"><div id="0" each="0">hola{hhh}</div></div></div></div>'
    c.a = False
    assert str(node) == '<div class="page"><div id="a" if="a"></div></div>'
    c.b = False
    assert str(node) == '<div class="page"><div id="a" if="a"></div></div>'
    c.b = True
    assert str(node) == '<div class="page"><div id="a" if="a"></div></div>'
    c.a = True
    assert str(node) == '<div class="page"><div id="a" if="a"><div id="b" if="b"><div id="0" each="0">hola{hhh}</div></div></div></div>'


def test_class_and_if_model():
    a = A(id=None, y=8, z=9, post='')
    node = jq("<div id='a'><div r id='0' class={hello}>{y}</div><div id='b' if='flag'><div r id='1'>{z}</div></div></div>")
    components.main.page.document = node
    class MyQuery(Query):
        reactives = []
    q = MyQuery('', '', None, 0, 1)
    parse(node, a, q)

    a.z = 11
    assert str(node) == '<div id="a"><div r="" id="0" class="hello world!">8</div><div id="b" if="flag"><div r="" id="1">11</div></div></div>'
    print('a.z=9')
    a.z = 9
    assert str(node) == '<div id="a"><div r="" id="0" class="hello world!">8</div><div id="b" if="flag"></div></div>'
    print('a.z=13')
    a.z = 13
    assert str(node) == '<div id="a"><div r="" id="0" class="hello world!">8</div><div id="b" if="flag"><div r="" id="1">13</div></div></div>'
    print('a.post x')
    a.post = 'x'
    assert str(node) == '<div id="a"><div r="" id="0" class="hello world!x">8</div><div id="b" if="flag"><div r="" id="1">13</div></div></div>'


def test_on_click_final():
    node = jq('<div id="0"><span id="if1" if="flag"><span r id="hoja1" on-click="click">{y}</span></span></div>')
    components.main.page.document = node
    a = A(id=None, y=0, z=19)

    #class MyController(PageController):
    #    reactives = []

    class MyQuery(Query):
        reactives = []

    #c = MyController()
    q = MyQuery('', '', None, 0, 1)

    parse(node, a, q)
    assert len(node.find('#hoja1')) == 1
    assert node.find('#hoja1').text() == '0'
    print('a.z=...1')
    a.z = 18
    print('a.z=...2')
    a.z = 9

    assert len(node.find('#hoja1')) == 0


def test_nested():
    node = jq('<div class="page"><div id="a" each="0"><div id="b" r>{f}</div><div id="c" each="1"><span id="d" r>{f}</span></div></div></div>')
    global document
    document = node
    components.main.page.document = node
    c = MyController(a=True, b=True)
    parse(node, c)
    print(node)
    assert False