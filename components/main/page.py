import re
from components.main.reactive import Model, reactive
from browser import window, document
import json

jq = window.jq


def is_alive(node):
    return jq.contains(document, node[0])


def if_function(controller, if_, node, html):
    print('if function', if_)
    if is_alive(node):
        val = getattr(controller, if_)
        if callable(val):
            val = val()
        print(val)
        if not val:
            for ch in node.find('[r]'):
                ch = jq(ch)
                if ch.data('helper'):
                    for c, h in ch.data('helper'):
                        c.reset(h)
            node.children().remove()
        else:
            if node.children().length == 0:
                children = jq(html)
                node.append(children)
                for ch in children:
                    parse(controller, jq(ch))
            elif node.children().length == 1:
                parse(controller, node.children())


def render(model, node, template):
    if template is None:
        return
    if is_alive(node):
        attrs = re.findall('\{[a-zA-Z_0-9]+\}', template)
        dct = {}
        for attr in attrs:
            attr = attr[1:-1]
            dct[attr] = getattr(model, attr)

        node.html(template.format(**dct))
        print('>', node.html())


def set_events(controller, node, attrs):
    print('set events', attrs)
    node.unbind() # debo intentar llamar a set_events sin necesidad de hacer unbind
    on_click = attrs.get('on-click')
    if on_click:
        on_click = on_click[1:-1]
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
        if node.children().length == 0:
            if node.attr('r') == '':
                helper = reactive(render, controller, node, node.html())
                lista = node.data('helper')
                if lista:
                    lista_ = []
                    for item in lista:
                        lista_.append(item)
                    lista_.append((controller, helper))
                    node.data('helper', lista_)
                else:
                    node.data('helper', [(controller, helper)])
        else:
            if node.hasClass('template'):
                controller.register(node)
            else:
                for ch in node.children():
                    ch = jq(ch)
                    parse(controller, ch)


class Controller(Model):
    objects = {}
    queries = {}

    def register(self, node):
        name = node.attr('query-id')
        html = node.html()
        node.children().remove()

        self.queries[name].nodes.append((node, html))
        for a in self.queries[name].models:
            n_ = jq(html)
            n_.attr('reactive_id', a.id)
            node.append(n_)
            parse(a, n_)

    def subscribe(self, q):
        name = q.id
        previous = Controller.queries.get(name)
        if previous:
            q.stop = previous.full_name
            q.nodes = previous.nodes
            for node, _ in q.nodes:
                if node.data('helper'):
                    for c, h in node.data('helper'):
                        c.reset(h)
                node.children().remove()
        Controller.queries[name] = q
        self.ws.send(q.dumps())

    def test(self, model, raw):
        query_full_name = raw['__query__']
        for query in self.queries.values():
            if query.full_name == query_full_name:
                print(raw)
                if '__out__' in raw.keys():
                    self.out(raw['__out__'], query)
                if '__new__' in raw.keys():
                    self.new(model, raw, query)
                if '__new__' not in raw.keys() and '__out__' not in raw.keys():
                    self.modify(model, raw, query)

    def modify(self, model, raw, query):
        index = self.index_by_id(model.id, query.models)
        del query.models[index]

        position = raw['__position__']
        if position == 'before':
            index = 0
        else:
            ref, index = position
        for node, html in query.nodes:
            n_ = node.children("[reactive_id='"+str(model.id)+"']")
            if position == 'before':
                node.prepend(n_)
            else:
                ref = node.children("[reactive_id='"+ref+"']")
                ref.after(n_)
            parse(model, n_)

        query.models.insert(index, model)

    def index_by_id(self, id, models):
        lista = []
        for item in models:
            lista.append(item.id)
        return lista.index(id)
        #return index_by_id(models, id)

    def out(self, _id, query):
        index = self.index_by_id(_id, query.models)
        del query.models[index]
        for node, html in query.nodes:
            node.children("[reactive_id='"+str(_id)+"']").remove()

    def new(self, model, raw, query):
        print('new', raw)
        ref, index = raw['__position__']
        #if position in ('before', 'append'):
        #    index = 0
        #else:
        #    ref, index = position
        query.models.insert(index, model)

        if ref == 'append':
            print('APPEND')
            for node, html in query.nodes:
                html = html.strip()
                n_ = jq(html)
                n_.attr('reactive_id', model.id)
                node.append(n_)
                parse(model, n_)
        elif ref == 'before':
            print('BEFORE')
            for node, html in query.nodes:
                html = html.strip()
                n_ = jq(html)
                n_.attr('reactive_id', model.id)
                node.prepend(n_)
                parse(model, n_)
        else:
            print('AFTER')
            for node, html in query.nodes:
                html = html.strip()
                n_ = jq(html)
                n_.attr('reactive_id', model.id)
                ref = node.children("[reactive_id='"+ref+"']")
                ref.after(n_)
                parse(model, n_)

