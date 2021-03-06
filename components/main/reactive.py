import random
import json
import re
from components.lib.epochdate import datetimeargs2epoch
from contextlib import contextmanager
from datetime import datetime

do_consume = True


def get_do_consume():
    return do_consume


@contextmanager
def execute_block():
    global do_consume
    do_consume = False
    try:
        yield
    finally:
        do_consume = True
        consume()

registered_models = {}
current_call = None


def get_current_call():
    global current_call
    return current_call


def reset_current_call():
    global current_call
    current_call = None

execute = []
map_ = {} # helper reative function to list of objects to reset


def add_to_map(obj):
    lista = map_.get(current_call, [])
    if obj not in lista:
        lista.append(obj)
    map_[current_call] = lista


def remove_helper_from_map(helper):
    if helper in map_.keys():
        del map_[helper]


def consume():
    while execute:
        call = execute.pop()
        call()


def reactive(func, *args, **kw):
    def helper():
        global current_call
        for c in map_.get(helper, []):
            c.reset(helper)
        remove_helper_from_map(helper)
        current_call = helper
        func(*args, **kw)
        current_call = None

    helper()
    return helper


def register(klass):
    registered_models[klass.__name__] = klass
    klass.objects = {}
    return klass


class Model(object):
    def __init__(self, **kw):
        if 'id' not in kw.keys() or kw['id'] is None:
            id = str(random.random())
        else:
            id = kw['id']
        self.__dict__['_dep'] = []
        self.__dict__['_dirty'] = set()
        self.__dict__['id'] = id
        self.__dict__['__collection__'] = self.__class__.__name__
        self.__dict__['caret'] = (0, 0)

        def set_values():
            for k, v in kw.items():
                if k in ('__deleted__', '__collection__'):
                    continue
                setattr(self, k, v)

        if do_consume:
            with execute_block():
                set_values()
        else:
            set_values()

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

    def __call__(self, *args, **kwargs):
        return self

    @staticmethod
    def integer_setter(value):
        val = re.sub(r'[^0-9]', '', value)
        return int(val)

    @staticmethod
    def integer_getter(value):
        return format(value, ',d')

    @staticmethod
    def phone_setter(value):
        return re.sub(r'[\(\)\- ]', '', value)

    @staticmethod
    def phone_getter(value):
        if len(value) < 3:
            return value
        else:
            tail = ''
            for i in range(3, len(value), 2):
                t1 = value[i]
                try:
                    t2 = value[i+1]
                except IndexError:
                    t2 = ''
                tail += t1 + t2 + ' '
            return ('('+value[0:3]+')-' + tail).rstrip()


    @staticmethod
    def datetime_setter(value):
        value_ = re.sub(r'-', '', value)
        try:
            return datetime.strptime(value_, '%d%m%Y')
        except ValueError:
            return value

    @staticmethod
    def datetime_getter(value):
        if type(value) is str:
            return value
        return value.strftime('%d-%m-%Y')

    def reset(self, func):
        ret = []
        for item in self._dep:
            if item['call'] != func:
                ret.append(item)
        self._dep = ret

    def __getattr__(self, name):
        if name in ('__set__', '__bool__', '__len__'): # investigar esto
            return

        if current_call is not None:
            self._dep.append({'call': current_call, 'attr': name})
            add_to_map(self)
        if '_'+name not in self.__dict__.keys():
            raise AttributeError(name)
        return self.__dict__['_'+name]

    def __setattr__(self, key, value):
        if key not in self.reactives:
            self.__dict__[key] = value
            return

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

            if do_consume:
                consume()


# ##########
class Reactive(object):
    reactives = []

    def __init__(self, **kw):
        self._dep = []

        def set_values():
            for k, v in kw.items():
                setattr(self, k, v)

        if do_consume:
            with execute_block():
                set_values()
        else:
            set_values()

    def __call__(self, *args, **kwargs):
        return self

    def reset(self, func):
        ret = []
        for item in self._dep:
            if item['call'] != func:
                ret.append(item)
        self._dep = ret

    def __getattr__(self, name):
        if name not in self.reactives:
            raise AttributeError(name)

        if current_call is not None:
            self._dep.append({'call': current_call, 'attr': name})
            add_to_map(self)

        return self.__dict__['_'+name]

    def __setattr__(self, key, value):
        if key not in self.reactives:
            self.__dict__[key] = value
            return

        if key in self.reactives and '_'+key not in self.__dict__.keys():
            self.__dict__['_'+key] = None

        if value != self.__dict__['_'+key]:
            self.__dict__['_'+key] = value
            for item in self._dep:
                if item['attr'] == key and item['call'] not in execute:
                    execute.append(item['call'])

            if do_consume:
                consume()