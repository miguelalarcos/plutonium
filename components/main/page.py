import re
from components.main.reactive import Model, reactive, Reactive
from browser import window, document
import json

jq = window.jq


def is_alive(node):
    return jq.contains(document, node[0])


def if_function(if_, node, html, *args):
    print('if function', if_)
    if is_alive(node):
        val = getattr(args[0], if_)
        if not val:
            print('flag', val)
            for ch in node.find('[r]'):
                ch = jq(ch)
                if ch.data('helper'):
                    for c, h in ch.data('helper'):
                        c.reset(h)
            node.children().remove()
        else:
                print('flag', val)
                children = jq(html)
                node.append(children)
                for ch in children:
                    parse(jq(ch), *args)


def render(node, template, *args):
    model = args[0]
    if template is None:
        return
    print('render')
    if is_alive(node):
        attrs = re.findall('\{[a-zA-Z_0-9]+\}', template)
        dct = {}
        for attr in attrs:
            attr = attr[1:-1]
            getter = None
            if ' ' in attr:
                attr, getter = attr.split()
            v = getattr(model, attr)
            if callable(v):
                v = v(*args[1:])
            if getter:
                v = getter(v)
            dct[attr] = v  # getattr(model, attr)

        node.html(template.format(**dct))
        print('>', node.html())


def set_events(node, attrs, *args):
    print('set events', attrs)

    controller = args[0]
    for action_str in ('on-click', 'on-keyup'):
        action = attrs.get(action_str)
        if action:
            method = getattr(controller, action)
            getattr(node, action_str[3:])(lambda: method(*args))

    if attrs.get('attr'):
        attr, getter, setter = attrs.get('attr').split()

        def helper(event):
            if event.which in (37, 39):
                return
            controller.caret = (node[0].selectionStart, len(node[0].value))
            val = node.val()
            s = getattr(controller, setter)
            val = s(val)
            setattr(controller, attr, val)
        node.keyup(helper)


def set_attributes(node, attrs, *args):
    controller = args[0]
    mapping = {}
    for key, value in attrs.items():
        if key in ('r', 'on-click', 'on-keyup'):
            continue
        if key == 'attr':
            attr, getter, setter = value.split()
            g = getattr(controller, getter)
            v = getattr(controller, attr)
            v = g(v)
            base = len(v) - controller.caret[1]
            node.val(v)
            node[0].setSelectionRange(controller.caret[0]+base, controller.caret[0]+base)
        else:
            attrs = re.findall('\{[a-zA-Z_0-9]+\}', value)
            for attr in attrs:
                attr = attr[1:-1]
                v = getattr(controller, attr)
                if callable(v):
                    v = v(*args[1:])
                mapping[attr] = v

            node.attr(key, value.format(**mapping))


#def parse(controller, node, query):
def parse(node, *args):
    controller = args[0]
    print('parse')
    if_ = node.attr('if')
    if if_:
        html = node.html()
        node.children().remove()
        helper = reactive(if_function, if_, node, html, *args)
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

            helper = reactive(set_attributes, node, dct, controller)
            node.data('helper', [(controller, helper)])
            set_events(node, dct, *args)
        if node.children().length == 0:
            if node.attr('r') == '':
                helper = reactive(render, node, node.html(), *args)
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
            if node.attr('each'):
                PageController.register(node, *args)
            else:
                for ch in node.children():
                    ch = jq(ch)
                    parse(ch, *args)


class PageController(Reactive):
    queries = {}

    @classmethod
    def register(cls, node, *args):
        name = node.attr('each')
        html = node.html()
        node.children().remove()

        q = cls.queries[name]
        q.node = (node, html)
        for a in q.models:
            n_ = jq(html)
            n_.attr('reactive-id', a.id)
            node.append(n_)
            parse(n_, a, q, *args)

    @classmethod
    def subscribe(cls, id, klass, name, sort, skip, limit, **kwargs):
        full_name = str((name, tuple(sorted([('__collection__', 'collection'),
                                            ('__sort__', sort), ('__skip__', skip)] +
                                            list(kwargs.items()) + [('__limit__', limit)]))))
        try:
            q = cls.queries[id]
            q.stop = q.full_name
            q.full_name = full_name
        except KeyError:
            q = klass(full_name, name, sort, skip, limit, **kwargs)
            cls.queries[id] = q

        if q.node:
            node, _ = q.node
            if node.data('helper'):
                for c, h in node.data('helper'):
                    c.reset(h)
            node.children().remove()
        cls.ws.send(q.dumps())
        return q

    @classmethod
    def test(cls, model, raw):
        query_full_name = raw['__query__']
        for query in cls.queries.values():
            if query.full_name == query_full_name:
                print(raw)
                if '__out__' in raw.keys():
                    cls.out(raw['__out__'], query)
                if '__new__' in raw.keys():
                    cls.new(model, raw, query)
                if '__new__' not in raw.keys() and '__out__' not in raw.keys():
                    cls.modify(model, raw, query)

    @classmethod
    def modify(cls, model, raw, query):
        index = cls.index_by_id(model.id, query.models)
        del query.models[index]

        position = raw['__position__']
        if position == 'before':
            index = 0
        else:
            ref, index = position
        for node, html in query.nodes:
            n_ = node.children("[reactive-id='"+str(model.id)+"']")
            if position == 'before':
                node.prepend(n_)
            else:
                ref = node.children("[reactive-id='"+ref+"']")
                ref.after(n_)
            parse(n_, model, query)

        query.models.insert(index, model)

    @staticmethod
    def index_by_id(id, models):
        lista = []
        for item in models:
            lista.append(item.id)
        return lista.index(id)

    @classmethod
    def out(cls, _id, query):
        index = cls.index_by_id(_id, query.models)
        del query.models[index]
        for node, html in query.nodes:
            node.children("[reactive-id='"+str(_id)+"']").remove()

    @classmethod
    def new(cls, model, raw, query):
        print('new', raw)
        ref, index = raw['__position__']
        query.models.insert(index, model)

        if ref == 'append':
            print('APPEND')
            for node, html in query.nodes:
                html = html.strip()
                n_ = jq(html)
                n_.attr('reactive-id', model.id)
                node.append(n_)
                parse(n_, model, query)
        elif ref == 'before':
            print('BEFORE')
            for node, html in query.nodes:
                html = html.strip()
                n_ = jq(html)
                n_.attr('reactive-id', model.id)
                node.prepend(n_)
                parse(n_, model, query)
        else:
            print('AFTER')
            for node, html in query.nodes:
                html = html.strip()
                n_ = jq(html)
                n_.attr('reactive-id', model.id)
                ref = node.children("[reactive-id='"+ref+"']")
                ref.after(n_)
                parse(n_, model, query)
