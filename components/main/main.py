import sys
sys.path.insert(0, 'http://localhost:8888/components')
sys.path.insert(0, 'http://localhost:8888/main/src/Lib')

from browser import window
jq = window.jQuery.noConflict(True)

window.jq = jq

import random
print('Iniciando aplicación')
from components.main.models.A import A
from components.main.init import init
from components.lib.filter_mongo import Filter

init()

from components.main.controller import Controller, SelectedModelControllerRef, BaseController
from components.main.filters import my_filter

filt = Filter({'__collection__': 'A', '__filter__': 'my_filter',
                                    'x': 5, 'y': 10, '__key__': [['x', -1], ], '__limit__': 2,
                                    '__skip__': 0})


class MyController(Controller):
    def first(self, model):
        self.touch
        if len(self.models) > 0 and self.models[0] is model:
            print('voy a retornar red')
            return 'red'
        print('voy a retornar vacio')
        return ''

c = MyController('container', filt)


def make_id():
    ret = ''
    for i in range(5):
        ret += str(random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]))
    return ret


def select_func(models):
    print('select func', models)
    if len(models) > 0:
        return models[0]
    return A(make_id(), x='')

smcr = SelectedModelControllerRef('first', c, select_func)

button_send = jq('#button')
sent_initial_data = False

def send_data():
    global sent_initial_data
    if not sent_initial_data:
        BaseController.subscribe_all()
        sent_initial_data = True
    #try:
    #    if random.random() < 0.5:
    #        obj = A(make_id(), x=random.randint(0, 10))
    #    else:
    #        obj = random.choice(list(A.objects.values()))
    #        obj.x = random.randint(0, 10)
    #except Exception as e:
    #    print ('-----------error:', e)
    #    obj = A(make_id(), x=random.randint(0, 10))
    #obj.save()


button_send.bind('click', send_data)



