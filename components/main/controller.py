import browser
window = browser.window
jq = window.jq # jQuery.noConflict(True)

from components.lib.filter_mongo import pass_filter
from components.main.reactive import reactive, get_current_call, execute, map_, reactive_first
import re
import json
from components.main.filter_ import filters


def render(model, node, template):
    print('render', model, node, template)
    #dct = {k[1:]: v for k, v in model.__dict__.items() if k.startswith('_')}
    dct = {}
    attrs = re.findall('\{[a-zA-Z_09]+\}', template)
    for attr in attrs:
        attr = attr[1:-1]
        v = getattr(model, attr)
        if callable(v):
            v = v()
        dct[attr] = v
    node.html(template.format(**dct))


def makeDIV(id, model, func, template):
    print('makeDIV', model, func, template)
    node = jq("<div reactive_id='"+str(id)+"'>test</div>")
    node.html(template)

    for n in node.find("[r]"):
        n_ = jq(n)
        reactive(model, func, n_, n_.html())
    return node


class FirstModelController(object):
    def __init__(self, name, controller):
        self.name = name
        self.controller = controller

        def f(controller, node, template):
            model = controller.first_model
            if model:
                render(model, node, template)

        self.node = jq('#'+self.name+' .template')
        reactive_first(self.controller, f, self.node, self.node.html())


class Controller(object):
    controllers = {}

    def __init__(self, name, key, filter, node=None, first=False):
        self.name = name
        self.models = []
        self.key = key
        name, kw = filter
        self.filter_json = {'__filter__': name}
        self.filter_json.update(kw)
        self.filter = filters[name](**kw)
        self.node = jq("[each='"+self.name+"']")
        self.node.id = self.node.attr('id')
        #self.node = node
        self.func = render
        self.first = first
        self.__class__.controllers[name] = self
        self._dep = []
        self._first = None

    @property
    def first_model(self):
        current_call = get_current_call()
        print('getter', current_call)
        if current_call is not None:
            self._dep.append({'call': current_call, 'attr': 'first'})
            r = map_.get(current_call, [])
            r.append(self)
            map_[current_call] = r
        return self._first

    @first_model.setter
    def first_model(self, model):
        print('setter')
        if self._first != model:
            print('self.model != model')
            self._first = model
            print('self._dep', self._dep)
            for item in self._dep:
                print('item', item)
                if item['attr'] == 'first' and item['call'] not in execute:
                    print('execute.append')
                    execute.append(item['call'])

    @classmethod
    def subscribe_all(cls):
        for c in cls.controllers.values():
            c.subscribe()

    def reset(self, func):
        ret = []
        for item in self._dep:
            if item['call'] != func:
                ret.append(item)
        self._dep = ret
        print('reset', self._dep)

    def subscribe(self, filter=None):
        if filter is None:
            print('sending filter', json.dumps(self.filter_json))
            self.ws.send(json.dumps(self.filter_json))
        else:
            name, kw = filter
            self.filter = filters[name](**kw)
            filter = {'__stop__': self.filter_json}
            self.filter_json = {'__filter__': name}.update(kw)
            self.ws.send(json.dumps(filter.update(self.filter_json)))

    def pass_filter(self, raw):
        return pass_filter(self.filter, raw)

    def test(self, model, raw):
        print('==>test', model, raw, model.id) # porbar con list([m.id for m in self.models])
        models = []
        for m in self.models:
            models.append(m.id)
        if model.id in models:
            print('esta dentro')
            if pass_filter(self.filter, raw):
                print('y permance dentro', 'MODIFY')
                self.modify(model)
                return False
            else:
                print('y sale', 'OUT')
                self.out(model)
                return True
        else:
            print('esta fuera')
            if pass_filter(self.filter, raw):
                print('y entra', 'NEW')
                self.new(model)
                return False
            else:
                print('y permanece fuera')
                return True #False

    def new(self, model):
        tupla = self.indexInList(model)
        print('tupla en new', tupla)
        index = tupla[0]

        self.models.insert(index, model)
        print('new: ', model, tupla)

        action = tupla[1]
        if action == 'append':
            print('append')
            node = makeDIV(model.id, model, self.func, jq('#'+str(self.node.id)+' .template').html())

            ref = jq('#'+str(self.node.id))
            ref.append(node)
            self.first_model = model
        elif action == 'before':
            node = makeDIV(model.id, model, self.func, jq('#'+str(self.node.id)+' .template').html())

            ref = jq('#'+str(self.node.id)).children("[reactive_id='"+str(tupla[2])+"']")

            ref.before(node)
            if self.first:
                ref.remove()
        elif action == 'after':
            if not self.first:
                node = makeDIV(model.id, model, self.func, jq('#'+str(self.node.id)+' .template').html())

                ref = jq('#'+str(self.node.id)).children("[reactive_id='"+str(tupla[2])+"']")
                ref.after(node)

    def out(self, model):
        index = self.indexById(model.id)
        del self.models[index]
        print ('out: ', model)

        node = jq('#'+str(self.node.id)).children("[reactive_id='"+str(model.id)+"']")
        node.remove()
        print('eliminado')
        if self.first and index == 0 and len(self.models) > 0:
            node = makeDIV(self.models[0].id, self.models[0], self.func, jq('#'+str(self.node.id)+' .template').html())
            ref = jq('#'+str(self.node.id))
            ref.append(node)

    def modify(self, model):
        index = self.indexById(model.id)
        del self.models[index]
        tupla = self.indexInList(model)
        if index == tupla[0]:
            print('ocupa misma posicion')
        elif self.first:
            if index == 0:
                jq('#'+str(self.node.id)).children("[reactive_id='"+str(model.id)+"']").remove()
                jq('#'+str(self.node.id)).append(makeDIV(self.models[0].id, self.models[0], self.func, jq('#'+str(self.node.id)+' .template').html()))
            elif tupla[0] == 0:
                jq('#'+str(self.node.id)).children("[reactive_id='"+str(self.models[0].id)+"']").remove()
                jq('#'+str(self.node.id)).append(makeDIV(model.id, model, self.func, jq('#'+str(self.node.id)+' .template').html()))
        else:
            print('move to ', model, tupla)

            node = jq('#'+str(self.node.id)).children("[reactive_id='"+str(model.id)+"']")
            node.remove()
            action = tupla[1]
            if action == 'before':
                ref = jq('#'+str(self.node.id)).children("[reactive_id='"+str(tupla[2])+"']")
                ref.before(node)
            elif action == 'after':
                ref = jq('#'+str(self.node.id)).children("[reactive_id='"+str(tupla[2])+"']")
                ref.after(node)

        self.models.insert(tupla[0], model)

    def indexById(self, id):
        index = 0
        for item in self.models:
            if item.id == id:
                break
            index += 1
        return index

    @staticmethod
    def compare(a, b, key, order='asc'):
        v_a = getattr(a, key)
        v_b = getattr(b, key)
        if v_a == v_b:
            return 0
        if v_a > v_b:
            if order == 'desc':
                return 1
            else:
                return -1
        if order == 'desc':
            return -1
        else:
            return 1

    def indexInList(self, model):
        if self.models == []:
            return (0, 'append')

        index = 0

        keys = self.key[:]
        key, order = keys.pop(0)
        flag = False
        for item in self.models:
            while True:
                ret = Controller.compare(model, item, key, order)
                if ret == 1:
                    flag = True
                    break
                if ret == 0:
                    if len(keys):
                        key, order = keys.pop(0)
                    else:
                        flag = True
                        break
                else:
                    break
            if flag:
                break
            index += 1
        if index == 0:
            return (index, 'before', self.models[0].id)
        else:
            return (index, 'after', self.models[index-1].id)
