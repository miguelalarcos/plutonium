import browser
window = browser.window
jq = window.jq

#from components.lib.filter_mongo import pass_filter
from components.main.reactive import reactive, get_current_call, execute, consume, add_to_map, get_do_consume, reset_current_call
import re
import json
from components.lib.filter_mongo import filters
from components.lib.utils import index_by_id, compare, index_in_list


def get_attrs_in_dict(attrs):
    ret = {}
    for attr in attrs:
        ret[attr.name] = attr.value
    return ret


def format_attr(m, attrs, c):
    dct = {}
    dct_ = {}

    for name, value in attrs.items():
        print('parejita', name, value)
        if type(value) is list:
            value = ' '.join(value)
        matches = re.findall('\{[a-zA-Z_0-9]+\}', value)
        for match in matches:
            match = match[1:-1]
            if hasattr(m, match):
                v = getattr(m, match)
            else:
                w = getattr(c, match)
                v = lambda: w(m)
            if callable(v) and name != 'on-click':
                v = v()
            dct_[match] = v

        dct[name] = value.format(**dct_)
    return dct


def set_attributes(n_, f_dct):
    dct = f_dct()
    print(dct)
    for item in n_[0].attributes:
        if item.name == 'value-integer':
            n_.val(dct['value-integer'])
            continue
        if item.name == 'on-click':
            continue

        if item.name in dct.keys():
            n_.attr(item.name, dct[item.name])


def render(n, m, c, template, attributes):
    print('*** render template', n, m, c, template)
    if callable(m):
        m = m()

    #if not m:
    #    return
#
    n.unbind()
    if n.attr('value-integer'): # solo cuando cambie el modelo
        def set_value(event):
            try:
                val = int(n.val())
            except ValueError:
                val = n.val()
            setattr(m, n.attr('value-integer')[1:-1], val)
        n.keyup(set_value)

    on_click = n.attr('on-click')
    if on_click:
        on_click = on_click[1:-1]
        if hasattr(m, on_click):
            method = getattr(m, on_click)
        else:
            method = lambda: getattr(c, on_click)(m)
        n.click(method)
#

    dct = {}
    attrs = re.findall('\{[a-zA-Z_0-9]+\}', template)

    for attr in attrs:
        attr = attr[1:-1]
        if hasattr(m, attr):
            v = getattr(m, attr)
        else:
            w = getattr(c, attr)
            v = lambda: w(m)
        if callable(v):
            v = v()

        dct[attr] = v

    n.html(template.format(**dct))
    set_attributes(n, lambda: format_attr(m, attributes, c))

    print('***render', n.html())

#
def helper(n, m, children, c, attributes):
    print('helper', n)
    fm = m
    if callable(m):
        m = m()

    v = True
    if n.attr('if'):
        attr = n.attr('if')[1:-1]
        v = getattr(m, attr)
        if callable(v):
            v = v()
        reset_current_call()
    if v:
        if not children:
            if n.attr('r') or n.attr('r') == '':
                attributes = get_attrs_in_dict(attributes)
                n.data('helper', reactive(render, n, fm, c, n.html(), attributes))  # n[0].outerHTML
        else:
            if n.attr('if'):
                if n.children().length == 0:
                    n.append(children)
                    n.children().first().removeClass('template')
                elif n.children().first().hasClass('template'):
                    n.children().first().removeClass('template')
                else:
                    return
            if n.attr('r') or n.attr('r') == '':
                attrs = get_attrs_in_dict(attributes)
                n.data('helper', reactive(set_attributes, n, lambda: format_attr(m, attrs, c)))

            for ch in children:
                render_ex(ch, fm)
    else:
        if n.children().first():
            for ch in n.find('[r]'):
                ch = jq(ch)
                if ch.data('helper'):
                    m.reset(ch.data('helper'))
            n.children().first().remove()

#
def render_ex(node, model, controller=None):
    #if not model:
    #    return
    """
    def _set_attributes(n_, f_dct):
        dct = f_dct()
        for item in n_[0].attributes:
            if item.name in ('value-integer', 'on-click'):
                continue

            if item.name in dct.keys():
                n_.attr(item.name, dct[item.name])

    def _render(n, m, c, template, attributes):
        print('*** render template', template)
        if callable(m):
            m = m()

        if not m:
            return
#
        n.unbind()
        if n.attr('value-integer'): # solo cuando cambie el modelo
            def set_value(event):
                try:
                    val = int(n.val())
                except ValueError:
                    val = n.val()
                setattr(m, n.attr('value-integer')[1:-1], val)
            n.keyup(set_value)
#
        on_click = n.attr('on-click')
        if on_click:
            on_click = on_click[1:-1]
            if hasattr(m, on_click):
                method = getattr(m, on_click)
            else:
                method = lambda: getattr(c, on_click)(m)
            n.click(method)
#
        attr_vi = n.attr('value-integer')
        dct = {}
        attrs = re.findall('\{[a-zA-Z_0-9]+\}', template)

        for attr in attrs:
            attr = attr[1:-1]
            if hasattr(m, attr):
                v = getattr(m, attr)
            else:
                w = getattr(c, attr)
                v = lambda: w(m)
            if callable(v):
                if attributes.get('on-click')[1:-1] != attr:
                    v = v()
                else:
                    v = attr  # ################################# no se que poner
            dct[attr] = v

        n.html(template.format(**dct))
        set_attributes(n, lambda: format_attr(m, attributes, c))
        if attr_vi:
            attr_vi = attr_vi[1:-1]
            n.val(dct[attr_vi])
        print('***render', n.html())

    def _helper(n, m, children, c, attributes):
        print('helper', n)
        fm = m
        if callable(m):
            m = m()

        v = True
        if n.attr('if'):
            attr = n.attr('if')[1:-1]
            v = getattr(m, attr)
            if callable(v):
                v = v()
            reset_current_call()
        if v:
            if not children:
                if n.attr('r') or n.attr('r') == '':
                    attributes = get_attrs_in_dict(attributes)
                    n.data('helper', reactive(render, n, fm, c, n.html(), attributes))  # n[0].outerHTML
            else:
                if n.attr('if'):
                    if n.children().length == 0:
                        n.append(children)
                        n.children().first().removeClass('template')
                    elif n.children().first().hasClass('template'):
                        n.children().first().removeClass('template')
                    else:
                        return
                if n.attr('r') or n.attr('r') == '':
                    attrs = get_attrs_in_dict(attributes)
                    n.data('helper', reactive(set_attributes, n, lambda: format_attr(m, attrs, c)))

                for ch in children:
                    render_ex(ch, fm)
        else:
            if n.children().first():
                for ch in n.find('[r]'):
                    ch = jq(ch)
                    print('3)')
                    print('3)', ch.data)
                    if ch.data('helper'):
                        m.reset(ch.data('helper'))
                n.children().first().remove()
    """
    children_ = []
    for n_ in node.children():
        children_.append(jq(n_))
    if node.attr('if'):
        reactive(helper, node, model, children_, controller, node[0].attributes)
    else:
        helper(node, model, children_, controller, node[0].attributes)


def makeDIV(model, template, controller=None):
    print('makeDIV')
    node = jq(template)
    node.removeClass('template')
    render_ex(node, model, controller)
    print('makeDIV retornamos node', node)
    return node


class BaseController(object):
    controllers = {}

    @classmethod
    def subscribe_all(cls):
        for c in cls.controllers.values():
            c.subscribe()

    def subscribe(self, filter_=None):
        if filter_ is None:
            self.ws.send(json.dumps(self.filter_json))
        else:
            self._set_filter(filter_)
            self.ws.send(json.dumps(self.filter_json))

    def indexById(self, id):
        return index_by_id(self.models, id)

    @staticmethod
    def compare(a, b, key, order=1):
        return compare(a, b, key, order)

    def indexInList(self, model):
        ret = index_in_list(self.models, self.key, model)
        if ret == 0 and self.models == []:
            return (0, 'append')
        if ret == 0:
            return (0, 'before', self.models[0].id)
        else:
            return (ret, 'after', self.models[ret-1].id)


class SelectedModelControllerRef(BaseController):
    def __init__(self, name, ref, selection_func=None):
        self.name = name
        self.ref = ref
        self.selected = None

        controller = ref
        def f():
            controller.touch
            model = selection_func(controller.models)
            self.selected = model  #
            return model

        self.node = jq('#'+self.name)
        render_ex(self.node, f)


class Controller(BaseController):

    def __init__(self, name, filter_):
        self.name = name
        self._set_filter(filter_)

        self.node = jq('#'+self.name)
        self.node.id = self.node.attr('id')
        self._dep = []
        self._touch = 0
        BaseController.controllers[self.name] = self

    def _set_filter(self, filter_):
        filter = filter_
        self.filter_object = filter
        self.limit = filter.limit
        self.filter_json = filter.raw_filter.copy()
        raw_filter = filter.raw_filter.copy()
        filter_name = filter.name
        self.filter_full_name = str([filter_name] + sorted(raw_filter.items()))

        self.models = []
        self.key = filter.key
        for attr in ('__key__', '__skip__', '__limit__', '__collection__'):
            if attr in raw_filter.keys():
                del raw_filter[attr]

        dct = raw_filter.copy()
        del dct['__filter__']
        self.filter = filters[filter_name](**dct)

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

    def pass_filter(self, raw):
        return self.filter_object.pass_filter(raw)

    def test_filter(self, ini):
        if len(self.models) > self.limit:
            if ini != self.models[0].id:
                self.out(self.models[0])
            else:
                self.out(self.models[-1])
        #elif not self.pass_filter(self.models[0]):
        #    self.out(self.models[0])
        #elif not self.pass_filter(self.models[-1]):
        #    self.out(self.models[-1])



    def test(self, model, raw):
        print('==>test', model, raw, model.id)
        models = []
        for m in self.models:
            models.append(m.id)
        if model.id in models:
            print('esta dentro')
            if self.pass_filter(raw):
                print('y permance dentro', 'MODIFY')
                self.modify(model)
                self.touch += 1
                return False
            else:
                print('y sale', 'OUT')
                self.out(model)
                self.touch += 1
                return True
        else:
            print('esta fuera')
            if self.pass_filter(raw):
                print('y entra', 'NEW')
                self.new(model, raw.get('__skip__'))
                self.touch += 1

                return False
            else:
                print('y permanece fuera')
                return True #False

    def new(self, model, i):
        tupla = self.indexInList(model)
        index = tupla[0]
        self.models.insert(index, model)

        action = tupla[1]
        if action == 'append':
            print('                APPEND')
            node = makeDIV(model, jq('#'+str(self.node.id)+' .template')[0].outerHTML, self)
            ref = jq('#'+str(self.node.id))
            ref.append(node)
        elif action == 'before':
            print('                BEFORE', tupla[2])
            node = makeDIV(model, jq('#'+str(self.node.id)+' .template')[0].outerHTML, self)
            ref = jq('#'+str(self.node.id)).children("[reactive_id='"+str(tupla[2])+"']")
            print('ref', '#'+str(self.node.id), str(tupla[2]))
            ref.before(node)
        elif action == 'after':
            print('                AFTER', tupla[2])
            node = makeDIV(model, jq('#'+str(self.node.id)+' .template')[0].outerHTML, self)
            ref = jq('#'+str(self.node.id)).children("[reactive_id='"+str(tupla[2])+"']")
            ref.after(node)

        self.test_filter(i)

    def out(self, model):
        index = self.indexById(model.id)
        del self.models[index]

        node = jq('#'+str(self.node.id)).children("[reactive_id='"+str(model.id)+"']")
        node.remove()

    def modify(self, model):
        index = self.indexById(model.id)
        del self.models[index]
        tupla = self.indexInList(model)
        if index == tupla[0]:
            print('ocupa misma posicion')
        else:
            print('move to ', model, tupla)
            node = jq('#'+str(self.node.id)).children("[reactive_id='"+str(model.id)+"']")

            #node.remove()
            action = tupla[1]
            if action == 'before':
                ref = jq('#'+str(self.node.id)).children("[reactive_id='"+str(tupla[2])+"']")
                ref.before(node)
            elif action == 'after':
                ref = jq('#'+str(self.node.id)).children("[reactive_id='"+str(tupla[2])+"']")
                ref.after(node)

        self.models.insert(tupla[0], model)

