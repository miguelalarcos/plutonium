import random
import json
print('R(1)')
from components.lib.epochdate import datetimeargs2epoch
print('R(2)')

registered_models = {}
current_call = None


def get_current_call():
    global current_call
    return current_call

execute = []
map_ = {} # function to list of objects to reset


def add_to_map(obj):
    lista = map_.get(current_call, [])
    if obj not in lista:
        lista.append(obj)
    map_[current_call] = lista

def consume():
    while execute:
        call = execute.pop()
        call()


def basic_reactive(func):
    def helper():
        global current_call
        for c in map_.get(helper, []):
            print('vamos a resetear')
            c.reset(helper)
        #del map_[helper]
        current_call = helper
        func()
        current_call = None

    helper()


def reactive_selected(controller, func, node, template):
    def helper():
        global current_call
        for c in map_.get(helper, []):
            c.reset(helper)
        #del map_[helper]
        current_call = helper
        print('calling func', controller, node, template)
        func(controller, node, template)
        current_call = None

    helper()


def reactive(model, func, node=None, template=None):
    def helper():
        global current_call
        model.reset(helper)  # es necesario?? supongo que cuando haga a Model insertar en map_, ya no sera necesario. Entonces podre unificar las dos def reactives
        for c in map_.get(helper, []):
            c.reset(helper)
        #del map_[helper]
        current_call = helper
        func(model, node, template)
        current_call = None

    helper()


def register(klass):
    registered_models[klass.__name__] = klass
    klass.objects = {}
    return klass


class Model(object):
    def __init__(self, id, **kw):
        if id is None:
            id = str(random.random())
        self.__dict__['_dep'] = []
        self.__dict__['_dirty'] = set()
        self.__dict__['id'] = id
        self.__dict__['__collection__'] = self.__class__.__name__
        for k,v in kw.items():
            if k in ('__deleted__', '__collection__'):
                continue
            setattr(self, k, v)

        self.__class__.objects[id] = self
        self.selected = False

    def validate(self):
        return all([getattr(self, m)() for m in dir(self.__class__) if m.startswith('validate_')])

    def save(self):
        if len(self._dirty) == 0:
            return
        dct = {}
        for k in self._dirty:
            dct[k] = getattr(self, k)
        data = {'id': self.id, '__collection__': self.__collection__}
        data.update(dct)
        self._dirty = set()
        print ('*** sending data', data)
        data = datetimeargs2epoch(data)
        Model.ws.send(json.dumps(data))

    def reset(self, func):
        ret = []
        for item in self._dep:
            if item['call'] != func:
                ret.append(item)
        self._dep = ret

    def __getattr__(self, name):
        if current_call is not None:
            self._dep.append({'call': current_call, 'attr': name})
            add_to_map(self)
        return self.__dict__['_'+name]

    def __setattr__(self, key, value):
        if key.startswith('_'):
            dirty = False
            key = key[1:]
        else:
            dirty = True

        if '_'+key not in self.__dict__.keys():
            self.__dict__['_'+key] = value
            if dirty:
                self._dirty.add(key)
            return

        if value != self.__dict__['_'+key]:
            self.__dict__['_'+key] = value
            if dirty:
                self._dirty.add(key)

            for item in self._dep:
                if item['attr'] == key and item['call'] not in execute:
                    execute.append(item['call'])
            consume()
