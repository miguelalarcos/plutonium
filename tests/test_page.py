import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
sys.modules['browser'] = Mock()
import re
from components.main.reactive import Model, reactive
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
        node = pq(node)
        id_ = node.attr('id') or 'None'
        return len(document.find('#'+id_))

pq = ExtendedPyQuery
document = None


def is_alive(node):
    return pq.contains(document, node[0])


def if_function(controller, if_, node, html):
    if is_alive(node):
        val = getattr(controller, if_)
        if callable(val):
            val = val()

        if not val:
            for ch in node.find('[r]'):
                ch = pq(ch)
                if ch.data('helper'):
                    for c, h in ch.data('helper'):
                        c.reset(h)
            node.children().remove()
        else:
            if len(node.children()) == 0:
                children = pq(html)
                node.append(children)
                for ch in children:
                    parse(controller, pq(ch))


def render(model, node, template):
    print('render:', template)
    if template is None:
        return
    if is_alive(node):
        attrs = re.findall('\{[a-zA-Z_0-9]+\}', template)
        dct = {}
        for attr in attrs:
            attr = attr[1:-1]
            dct[attr] = getattr(model, attr)

        node.html(template.format(**dct))
        #print('>', node)


def set_events(controller, node, attrs):
    on_click = attrs.get('on-click')
    if on_click:
        on_click = on_click[1:-1]
        print(attrs, on_click)
        method = getattr(controller, on_click)
        node.click(method)
    integer_value = attrs.get('integer-value')
    if integer_value:
        integer_value = integer_value[1:-1]

        def set_integer_value(event=None):
            try:
                val = int(node.val())
            except ValueError:
                val = node.val()
            setattr(controller, integer_value, val)
        node.keyup(set_integer_value)


def set_attributes(controller, node, attrs):
    mapping = {}
    for key, value in attrs.items():
        if key == 'r':
            continue
        attrs = re.findall('\{[a-zA-Z_0-9]+\}', value)
        for attr in attrs:
            attr = attr[1:-1]
            v = getattr(controller, attr)
            if callable(v) and key != 'on-click':
                v = v()
            if key == 'integer-value':
                node.val(str(v))

            mapping[attr] = v
        if key not in ('on-click', 'integer-value'):
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
                dct = {}
                for k, v in node[0].attrib.items():
                    dct[k] = v

            helper = reactive(set_attributes, controller, node, dct)
            node.data('helper', [(controller, helper)])
            set_events(controller, node, dct)
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
        return 'hello world!' + self.post

    def click(self):
        print('click')


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
    a = A(id=None, y=8, z=9, post='')
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
    print('a.post x')
    a.post = 'x'
    assert str(node) == '<div id="a" class="template"><div r="" id="0" class="hello world!x">8</div><div id="b" if="{h}"><div r="" id="1">13</div></div></div>'


def test_on_click():
    a = A(id=None, y=8)
    node = pq("<div id='a' class='template'><div r id='0' on-click={click}>{y}</div></div>")
    global document
    document = node
    parse(a, node)

    n = node.find('#0')
    n.click()
    #assert False


def test_integer_value():
    a = A(id=None, y=8)
    node = pq("<div id='a' class='template'><input r id='0' integer-value={y}></div>")
    global document
    document = node
    parse(a, node)

    n = node.find('#0')
    assert n.val() == '8'
    n.val('10')
    n.keyup()
    assert a.y == 10