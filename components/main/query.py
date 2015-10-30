import json
from components.main.reactive import Reactive, reactive
from browser import window, document

jq = window.jq

registered_queries = {}


def register(Q):
    registered_queries[Q.__name__] = Q
    return Q


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


class QueryTemplate:
    templates = {}

    def __init__(self, name, sort, skip, limit):
        self.name = name
        self.sort = sort
        self.skip = skip
        self.limit = limit
        QueryTemplate.templates[name] = self


class Query(Reactive):
    queries = {}

    def __init__(self, node, html, name, **kwargs):
        super().__init__(**kwargs)
        self.full_name = name + str(sorted(list(kwargs.items())))
        print (self.full_name)
        Query.queries[self.full_name] = self
        self.node = node
        self.html = html.strip()
        self.name = name
        self.kwargs = kwargs

    def stop(self):
        print('query stop')

    def append(self, model):
        n = jq(self.html)
        self.node.append(n)
        parse(n, model)


def parse(node, model):
    #print('parse', model, node)
    if node.attr('each'):
        query = node.attr('each')

        @reactive
        def r():
            #params = node.attr('params')
            #params = getattr(model, params)()
            params = {}
            for k, v in node[0].attrib.items():
                if k.startswith('param_'):
                    params[k[6:]] = getattr(model, k[6:])
            q = Query(node, node.html(), query, **params)
            node.data('query', q)
            clear(node)
        return

    if node.attr('r') == '':
        print('reactividad', model)
        node.data('reactivity', (model, '0'))

    for ch in node.children():
        parse(jq(ch), model)


def clear(node):
    print('clear')
    for ch in node.find('*'):
        ch = jq(ch)
        if ch.data('reactivity'):
            c, h = ch.data('reactivity')
            c.reset(h)
        if ch.data('query'):
            print('data query', ch.data('query'))
            ch.data('query').stop()
    node.children().remove()


