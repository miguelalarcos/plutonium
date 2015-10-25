import sys
sys.path.insert(0, '.')

from mock import Mock
browser_mock = Mock()
sys.modules['browser'] = browser_mock

from components.main.reactive import Model, reactive, Reactive
from components.main.page import Query, PageController

import time


def reactive_property(f):
    return property(f)


class A(Model):
    objects = {}


class BaseQueryPattern(Query):
    _collection = 'B'

    def query(self):
        return {'surname': {'regex': self.pattern}}

class BaseQuery(Query):
    _collection = 'A'

    def query(self):
        return {'x': {'$gte': self.a, '$lte': self.b}}


class MyQuery(BaseQuery):
    reactives = ['focused', ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.models = [A(id=None, x=-1), A(id=None, x=-2), A(id=None, x=-3)]
        self.focused = self.models[0]

        class Helper(Reactive):
            reactives = ['x']
        self.keyup = Helper(x=None)

    def react(self, controller):
        @reactive
        def r():
            qs = controller.qs
            if qs.selected:
                self.focused.x = qs.selected.x


class QuerySearch(BaseQueryPattern):
    reactives = ['focused', 'selected']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.models = [A(id=None, x=0), A(id=None, x=1), A(id=None, x=2)]
        self.focused = self.models[0]
        self.selected = None
        self.index_focused = 0

    def react(self, controller):
        @reactive
        def r():
            self.on_key_up(controller.q.keyup.x)

    def on_key_up(self, key):
        if key is None:
            return

        if key[0] == 'up':
            self.index_focused += 1
        elif key[0] == 'down':
            self.index_focused -= 1
        else:
            self.selected = self.focused

        if self.index_focused == len(self.models):
            self.index_focused = 0
        if self.index_focused == -1:
            self.index_focused = len(self.models)-1
        self.focused = self.models[self.index_focused]


class MyController(PageController):
    ws = Mock()

    def __init__(self, id, **kwargs):
        super().__init__(id, **kwargs)
        #self.queries = {}

        @reactive
        def r():
            self.q = self.subscribe(id='my_query', klass=MyQuery, name='between', sort=(('x', 1),), skip=0, limit=1, a=self.a, b=self.b)


        @reactive
        def r():
            self.qs = self.subscribe(id='my_query_search', klass=QuerySearch, name='search', sort=(('name', 1),), skip=0, limit=10, pattern=self.q.focused.x)

    # def subscribe(self, id, klass, name, sort, skip, limit, **kwargs):
    #     if id in self.queries.keys():
    #         print('stop', self.queries[id].full_name)
    #     print('subscribe', kwargs)
    #     full_name = str((name, tuple(sorted([('__collection__', 'collection'),
    #                                             ('__sort__', sort), ('__skip__', skip)] +
    #                                              list(kwargs.items()) + [('__limit__', limit)]))))
    #     try:
    #         q = self.queries[id]
    #         q.full_name = full_name
    #         return q
    #     except KeyError:
    #         q = klass(full_name)
    #         self.queries[id] = q
    #         return q


def test_0():
    a = A(id=None, z=900)

    @reactive
    def r():
        print(a.z)

    a.z = 901

    assert False

def __test_0():
    page_controller = MyController(id='my controller', a=1, b=10)
    page_controller.q.react(page_controller)
    page_controller.qs.react(page_controller)

    page_controller.a = 5
    page_controller.q.focused.x = 'hola'
    page_controller.q.keyup.x = ('up', time.time())
    page_controller.q.keyup.x = ('up', time.time())
    page_controller.q.keyup.x = ('enter', time.time())
    assert page_controller.q.focused.x == 2
    assert False