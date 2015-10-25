import re
from components.main.reactive import Model, reactive, Reactive
from browser import window, document
import json

jq = window.jq


def is_alive(node):
    return jq.contains(document, node[0])


def if_function(controller, if_, node, html, query):
    print('if function', if_)
    if is_alive(node):
        val = getattr(controller, if_)
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
                    parse(controller, jq(ch), query)


def render(model, node, template):
    if template is None:
        return
    print('render')
    if is_alive(node):
        attrs = re.findall('\{[a-zA-Z_0-9]+\}', template)
        dct = {}
        for attr in attrs:
            attr = attr[1:-1]
            dct[attr] = getattr(model, attr)

        node.html(template.format(**dct))
        print('>', node.html())


def set_events(controller, node, attrs, query):
    print('set events', attrs)
    #node.unbind()
    on_click = attrs.get('on-click')
    if on_click:
        on_click = on_click[1:-1]
        method = getattr(controller, on_click)
        node.click(lambda: method(query))

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


def set_attributes(controller, node, attrs):
    mapping = {}
    for key, value in attrs.items():
        if key == 'r':
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
                if callable(v) and key != 'on-click':
                    v = v()
                #if key == 'integer-value':
                #    node.val(str(v))

                mapping[attr] = v
            if key not in ('on-click', 'integer-value'):
                node.attr(key, value.format(**mapping))


def parse(controller, node, query):
    print('parse')
    if_ = node.attr('if')
    if if_:
        if_ = if_[1:-1]
        html = node.html()
        node.children().remove()
        helper = reactive(if_function, controller, if_, node, html, query)
        node.data('helper', [(controller, helper)])
    else:
        print(node)
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
            set_events(controller, node, dct, query)
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
                    parse(controller, ch, query)


class _Controller(Model):
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


class Query(Reactive):
    def __init__(self, full_name, name, sort, skip, limit, **kwargs):
        super().__init__(**kwargs)
        self.full_name = full_name
        self.name = name
        self.sort = sort
        self.skip = skip
        self.limit = limit
        self.kw = kwargs
        self.stop = None
        self.models = []
        self.node = None

    def dumps(self):
        arg = {}
        arg['__query__'] = self.name
        arg['__sort__'] = self.sort
        arg['__skip__'] = self.skip
        arg['__limit__'] = self.limit
        if self.stop:
            arg['__stop__'] = self.stop
        for k, v in self.kw.items():
            arg[k] = v
        return json.dumps(arg)


class PageController(Reactive):
    queries = {}

    def register(self, node):
        name = node.attr('query-id')
        html = node.html()
        node.children().remove()

        q = self.queries[name]
        q.node = (node, html)
        for a in q.models:
            n_ = jq(html)
            n_.attr('reactive_id', a.id)
            node.append(n_)
            parse(a, n_, q)

    def subscribe(self, id, klass, name, sort, skip, limit, **kwargs):
        full_name = str((name, tuple(sorted([('__collection__', 'collection'),
                                            ('__sort__', sort), ('__skip__', skip)] +
                                            list(kwargs.items()) + [('__limit__', limit)]))))
        try:
            q = self.queries[id]
            q.stop = q.full_name
            q.full_name = full_name
        except KeyError:
            q = klass(full_name, name, sort, skip, limit, **kwargs)
            self.queries[id] = q

        if q.node:
            node, _ = q.node
            if node.data('helper'):
                for c, h in node.data('helper'):
                    c.reset(h)
            node.children().remove()
        self.ws.send(q.dumps())
        return q

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
            parse(model, n_, query)

        query.models.insert(index, model)

    def index_by_id(self, id, models):
        lista = []
        for item in models:
            lista.append(item.id)
        return lista.index(id)

    def out(self, _id, query):
        index = self.index_by_id(_id, query.models)
        del query.models[index]
        for node, html in query.nodes:
            node.children("[reactive_id='"+str(_id)+"']").remove()

    def new(self, model, raw, query):
        print('new', raw)
        ref, index = raw['__position__']
        query.models.insert(index, model)

        if ref == 'append':
            print('APPEND')
            for node, html in query.nodes:
                html = html.strip()
                n_ = jq(html)
                n_.attr('reactive_id', model.id)
                node.append(n_)
                parse(model, n_, query)
        elif ref == 'before':
            print('BEFORE')
            for node, html in query.nodes:
                html = html.strip()
                n_ = jq(html)
                n_.attr('reactive_id', model.id)
                node.prepend(n_)
                parse(model, n_, query)
        else:
            print('AFTER')
            for node, html in query.nodes:
                html = html.strip()
                n_ = jq(html)
                n_.attr('reactive_id', model.id)
                ref = node.children("[reactive_id='"+ref+"']")
                ref.after(n_)
                parse(model, n_, query)
