import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
sys.modules['browser'] = Mock()
import re
from components.main.reactive import Model, reactive
from pyquery import PyQuery
import random

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
        if len(document.find('#'+id_)):
            return True
        rid = node.attr('reactive_id') or 'None'
        if len(document.find("[reactive_id='" + rid + "']")):
            return True
        return False

pq = ExtendedPyQuery
jq = pq
document = None


def is_alive(node):
    return pq.contains(document, node[0])


def if_function(controller, if_, node, html):
    print('if function', if_, node)
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
            elif len(node.children()) == 1:
                parse(controller, node.children())


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
    print('parse', node)
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
            if node.hasClass('template'):
                controller.register(node)
            else:
                for ch in node.children():
                    ch = pq(ch)
                    parse(controller, ch)


class Query(object):
    def __init__(self, id, sort, skip, limit, **kw):
        self.id = id
        self.full_name = str((self.__class__.__name__, tuple(sorted([('__collection__', self._collection),
                                                                     ('__sort__', sort), ('__skip__', skip)] +
                                                                    list(kw.items()) + [('__limit__', limit)]))))
        self.sort = sort
        self.skip = skip
        self.limit = limit
        for k,v in kw.items():
            setattr(self, k, v)
        self.models = [A(id=None, x=random.randint(0, 999))]
        self.nodes = []


class MyQuery(Query):
    _collection = 'A'

    def query(self):
        return {'x': {'$gte': self.a, '$lte': self.b}}


class Controller(Model):
    objects = {}
    queries = {}

    def __init__(self, id, **kwargs):
        Model.__init__(self, id, **kwargs)

        @reactive
        def f():
            q = MyQuery(id='0', sort=(('x', 1),), skip=0, limit=1, a=self.a, b=self.b)
            self.subscribe(q)

    def x(self):
        return False

    def register(self, node):
        name = node.attr('query-id')
        html = node.html()
        node.children().remove()
        self.queries[name].nodes.append((node, html))
        for a in self.queries[name].models:
            n_ = pq(html)
            n_.attr('reactive_id', a.id)
            node.append(n_)
            parse(a, n_)

    def subscribe(self, q):
        name = q.id
        previous = Controller.queries.get(name)
        if previous:
            print('stop subscription')
            q.nodes = previous.nodes
            for node, _ in q.nodes:
                if node.data('helper'):
                    for c, h in node.data('helper'):
                        c.reset(h)
                node.children().remove()
        Controller.queries[name] = q

    def test(self, model, raw, query_full_name):
        for query in self.queries.values():
            if query.full_name == query_full_name:
                if '__new__' in raw.keys():
                    self.new(model, raw, query)
                elif '__out__' in raw.keys():
                    self.out(model, query)
                else:
                    self.modify(model, query)

    def modify(self, model, query):
        index = self.index_by_id(model.id)
        del query.models[index]
        tupla = self.index_in_DOM(model)

        if index == tupla[0]:
            print('ocupa misma posicion')
        else:
            print('move to ', model, tupla)
            for node, html in query.nodes:
                n_ = node.children("[reactive_id='"+str(model.id)+"']")
                ref = node.children("[reactive_id='"+str(tupla[2])+"']")
                action = tupla[1]
                if action == 'before':
                    ref.before(n_)
                else:
                    ref.after(n_)
                parse(model, n_)

        query.models.insert(tupla[0], model)

    def out(self, model, query):
        index = self.index_by_id(model.id, query.models)
        del query.models[index]
        for node, html in query.nodes:
            node.children("[reactive_id='"+str(model.id)+"']").remove()

    def new(self, model, raw, query):
        tupla = self.index_in_DOM(model)
        index = tupla[0]
        query.models.insert(index, model)

        action = tupla[1]
        if action == 'append':
            for node, html in query.nodes:
                n_ = jq(html)
                n_.attr('reactive_id', model.id)
                node.append(n_)
                parse(model, n_)
        elif action == 'before':
            for node, html in query.nodes:
                n_ = jq(html)
                n_.attr('reactive_id', model.id)
                ref = node.children("[reactive_id='"+str(tupla[2])+"']")
                ref.before(n_)
                parse(model, n_)
        elif action == 'after':
            for node, html in query.nodes:
                n_ = jq(html)
                n_.attr('reactive_id', model.id)
                ref = node.children("[reactive_id='"+str(tupla[2])+"']")
                ref.after(n_)
                parse(model, n_)

        if len(query.models) > query.limit:
            if raw['__skip__'] != query.models[0].id:
                self.out(query.models[0])
            else:
                self.out(query.models[-1])

    def append(self, model, query_full_name):
        for query in self.queries.values():
            if query.full_name == query_full_name:
                query.models.append(model)
                for node, html in query.nodes:
                    n_ = pq(html)
                    n_.attr('reactive_id', model.id)
                    node.append(n_)
                    parse(model, n_)


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


def test_class_and_if_model():
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


def test_register():
    node = pq('<div class="page"><div id="0" query-id="0" class="template"><span r>{x}</span></div></div>')
    global document
    document = node
    c = Controller(id=None, a=0, b=10)
    parse(c, node)
    print(node)
    c.a = 1
    print('->', node)
    a = A(id=None, x=-1)
    c.append(a, "('MyQuery', (('__collection__', 'A'), ('__limit__', 1), ('__skip__', 0), ('__sort__', (('x', 1),)), ('a', 1), ('b', 10)))")
    print(node)
    assert False