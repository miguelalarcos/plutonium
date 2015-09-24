import browser
window = browser.window
jq = window.jq

from components.lib.filter_mongo import pass_filter
from components.main.reactive import reactive, get_current_call, execute, consume, add_to_map, get_do_consume
import re
import json
from components.main.filter_ import filters


def render(model, node, template): # ver si puedo quitar el argumento template y sustituirlo por node.outerHTML
    print('*** render', model, node, template)
    print('**** render', model.__dict__)
    dct = {}
    attrs = re.findall('\{[a-zA-Z_09]+\}', template)
    for attr in attrs:
        attr = attr[1:-1]
        v = getattr(model, attr)
        print(attr, v, model)
        if callable(v):
            v = v()
        dct[attr] = v

    node.html(node.html().format(**dct))
    for item in node[0].attributes:
        node.attr(item.name, item.value.format(**dct))


def makeDIV(id, model, func, template, controller=None):

    #node = jq("<div reactive_id='"+str(id)+"'>test</div>")
    #node.html(template)
    node = jq(template)  # ojo el template original debe llevar reactive_id='{id}'

    for n in node.find("[r]"):
        n_ = jq(n)
        on_click = n_.attr('on-click')
        if on_click:
            try:
                method = getattr(model, on_click)
                n_.click(method)
            except AttributeError:
                method = getattr(controller, on_click)
                n_.click(lambda: method(model))
        reactive(func, model, n_, n_.outerHTML())
    return node


class BaseController(object):
    controllers = {}

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


class SelectedModelController(BaseController):
    def __init__(self, name, key, filter_, selection_func):
        self.name = name
        self.key = key
        name, kw = filter_
        self.filter = filters[name](**kw)
        self.models = []
        self._dep = []
        self.selected = None
        self._touch = 0
        self.selection_func = selection_func
        BaseController.controllers[self.name] = self

        def f(controller, node, template):
            controller.touch
            model = controller.selection_func(controller.models)
            self.selected = model
            #for m in controller.models:
            #    m.selected

            if model:
                render(model, node, template)

        self.node = jq('#'+self.name+' .template')
        for n in self.node.find('[r]'):
            n_ = jq(n)
            on_click = n_.attr('on-click')
            if on_click:
                method = lambda: getattr(self.selected, on_click)
                n_.click(method)
            reactive(f,self, n_, n_.outerHTML())

    @property
    def touch(self):
        current_call = get_current_call()
        if current_call is not None:
            self._dep.append({'call': current_call, 'attr': 'touch'})
            add_to_map(self)
        return self._touch

    @touch.setter
    def touch(self, model):
        if self._touch != model:
            self._touch = model
            for item in self._dep:
                if item['attr'] == 'touch' and item['call'] not in execute:
                    execute.append(item['call'])
            if get_do_consume():
                consume()

    def reset(self, func):
        print('reset', func)
        ret = []
        for item in self._dep:
            if item['call'] != func:
                ret.append(item)
        self._dep = ret

    def test(self, model, raw):
        models = []
        for m in self.models:
            models.append(m.id)
        if model.id in models:
            print('esta dentro')
            if pass_filter(self.filter, raw):
                print('y permance dentro', 'MODIFY')
                index = self.indexById(model.id)
                del self.models[index]
                tupla = self.indexInList(model)
                self.models.insert(tupla[0], model)
                #self.selected = self.selection_func(self.models)
                self.touch += 1
                return False
            else:
                print('y sale', 'OUT')
                index = self.indexById(model.id)
                del self.models[index]
                #self.selected = self.selection_func(self.models)
                self.touch += 1
                model.selected = False
                return True
        else:
            print('esta fuera')
            if pass_filter(self.filter, raw):
                print('y entra', 'NEW')
                tupla = self.indexInList(model)
                self.models.insert(tupla[0], model)
                #self.selected = self.selection_func(self.models)
                self.touch += 1
                return False
            else:
                print('y permanece fuera')
                return True #False


class Controller(BaseController):

    def __init__(self, name, key, filter):
        self.name = name
        self.models = []
        self.key = key
        name, kw = filter
        self.filter_json = {'__filter__': name}
        self.filter_json.update(kw)
        self.filter = filters[name](**kw)
        self.node = jq("[each='"+self.name+"']")
        self.node.id = self.node.attr('id')
        self.func = render
        BaseController.controllers[self.name] = self

    @classmethod
    def subscribe_all(cls):
        for c in cls.controllers.values():
            c.subscribe()

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
        print('==>test', model, raw, model.id)
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
            node = makeDIV(model.id, model, self.func, jq('#'+str(self.node.id)+' .template').outerHTML(), self)

            ref = jq('#'+str(self.node.id))
            ref.append(node)
            #self.first_model = model
        elif action == 'before':
            node = makeDIV(model.id, model, self.func, jq('#'+str(self.node.id)+' .template').outerHTML(), self)
            ref = jq('#'+str(self.node.id)).children("[reactive_id='"+str(tupla[2])+"']")
            ref.before(node)
        elif action == 'after':
            node = makeDIV(model.id, model, self.func, jq('#'+str(self.node.id)+' .template').outerHTML(), self)

            ref = jq('#'+str(self.node.id)).children("[reactive_id='"+str(tupla[2])+"']")
            ref.after(node)

    def out(self, model):
        index = self.indexById(model.id)
        del self.models[index]
        print ('out: ', model)

        node = jq('#'+str(self.node.id)).children("[reactive_id='"+str(model.id)+"']")
        node.remove()
        print('eliminado')

    def modify(self, model):
        index = self.indexById(model.id)
        del self.models[index]
        tupla = self.indexInList(model)
        if index == tupla[0]:
            print('ocupa misma posicion')
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

