import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
sys.modules['browser'] = Mock()
import re
from components.main.reactive import Model, reactive
from utils import Node
#from browser import document
from pyquery import PyQuery


class ExtendedPyQuery(PyQuery):
    _data = {}

    def data(self, key, data=None):
        if data is None:
            return ExtendedPyQuery._data.get(self.attr('id'))
        ExtendedPyQuery._data[self.attr('id')] = data

    @staticmethod
    def contains(document, node):
        node = pq(node)
        id_ = node.attr('id') or 'None'
        print('#'+id_)
        return len(document.find('#'+id_))

pq = ExtendedPyQuery

jq = Mock()
ret = [True, True, True, True, True, False, True, True, True]


def side_effect(doc, n_):
    return ret.pop(0)


#jq.contains.side_effect = side_effect

document = None


def is_alive(node):
    return pq.contains(document, node[0])


def if_function(controller, if_, node, html):
    if is_alive(node):
        val = getattr(controller, if_)
        if callable(val):
            val = val()
        print(val)
        if not val:
            for ch in node.find('[r]'):
                ch = pq(ch)
                if ch.data('helper'):
                    #c, h = ch.data('helper')
                    for c, h in ch.data('helper'):
                        c.reset(h)
            #for ch in node.children():  # node.children().remove()
            #    pq(ch).remove()
            node.children().remove()
        else:
            if len(node.children()) == 0:
                children = pq(html)
                node.append(children)
                for ch in children:
                    print('-->', pq(ch))
                    parse(controller, pq(ch))


def render(model, node, template):
    print('template', template)
    if is_alive(node):
        attrs = re.findall('\{[a-zA-Z_0-9]+\}', template)
        dct = {}
        for attr in attrs:
            attr = attr[1:-1]
            dct[attr] = getattr(model, attr)

        node.html(template.format(**dct))
        print('>', node)


def set_attributes(controller, node, attrs):
    mapping = {}
    for key, value in attrs.items():
        if key == 'r':
            continue
        attrs = re.findall('\{[a-zA-Z_0-9]+\}', value)
        for attr in attrs:
            attr = attr[1:-1]
            v = getattr(controller, attr)
            if callable(v):
                v = v()
            mapping[attr] = v
        node.attr(key, value.format(**mapping))


def parse(controller, node):
    if_ = node.attr('if')
    if if_:
        if_ = if_[1:-1]
        helper = reactive(if_function, controller, if_, node, node.html())
        node.data('helper', [(controller, helper)])
    else:
        if node.attr('r') == '':
            try:
                dct = {}
                for attr in node[0].attributes:
                    dct[attr.name] = attr.value
            except AttributeError:
                dct = node[0].attrib

            helper = reactive(set_attributes, controller, node, dct)
            node.data('helper', [(controller, helper)])
        if len(node.children()) == 0:
            if node.attr('r') == '':
                helper = reactive(render, controller, node, node.html())
                lista = node.data('helper')
                if lista:
                    lista.append((controller, helper))
                else:
                    node.data('helper', [(controller, helper)])
        else:
            for ch in node.children():
                ch = pq(ch)
                if ch.hasClass('template'):
                    # register
                    pass
                else:
                    parse(controller, ch)


class Controller(Model):
    objects = {}

    def x(self):
        return False


class A(Model):
    objects = {}

    def h(self):
        return self.z != 9

    def hello(self):
        return 'hello world!'


def test_0():
    node = pq("<div class='page'><div id='a' if={x}><div id='t1' class='template'><div r id='0'>{y}</div><div r id='1'>{z}</div></div></div></div>")
    global document
    document = node
    parse(Controller(id=None), node)
    assert str(node) == '<div class="page"><div id="a" if="{x}"/></div>'


def test_if_if():
    node = pq('<div class="page"><div id="a" if="{a}"><div id="b" if="{b}"><div id="0" class="template">hola{hhh}</div></div></div></div>')
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


def test_1():
    a = A(id=None, y=8, z=9)
    node = pq("<div id='a' class='template'><div r id='0' class={hello}>{y}</div><div id='b' if={h}><div r id='1'>{z}</div></div></div>")
    global document
    document = node
    parse(a, node)

    a.z = 11
    assert str(node) == '<div id="a" class="template"><div r="" id="0" class="hello world!">8</div><div id="b" if="{h}"><div r="" id="1">11</div></div></div>'
    print('a.z=9')
    a.z = 9
    assert str(node) == '<div id="a" class="template"><div r="" id="0" class="hello world!">8</div><div id="b" if="{h}"></div></div>'
    print('a.z=13')
    a.z = 13
    assert str(node) == '<div id="a" class="template"><div r="" id="0" class="hello world!">8</div><div id="b" if="{h}"><div r="" id="1">13</div></div></div>'
