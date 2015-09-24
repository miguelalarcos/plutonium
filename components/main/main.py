import sys
sys.path.insert(0, 'http://localhost:8888/components')

from browser import window
jq = window.jQuery.noConflict(True)
print('jq:', jq)
window.jq = jq

import random
print('Iniciando aplicación')
from components.main.models.A import A
from components.main.init import init

init()

from components.main.controller import Controller, SelectedModelController
from components.main.filters import my_filter

key = [('x', 'desc')]
filter = ('my_filter', {'x': 5, 'y': 10})
Controller('MyController', key, filter)


def select_func(models):
    if len(models) > 0:
        return models[0]
    return A(x=0)

SelectedModelController('first', key, filter, select_func)

button_send = jq('#button')
sent_initial_data = False


def send_data():
    global sent_initial_data
    if not sent_initial_data:
        #Controller('MyController', key, filter)
        Controller.subscribe_all()
        sent_initial_data = True
    try:
        if random.random() < 0.5:
            obj = A(None, x=random.randint(0, 10))
        else:
            obj = random.choice(list(A.objects.values()))
            print('*** random choice object')
            obj.x = random.randint(0, 10)
    except Exception as e:
        print ('-----------error:', e)
        obj = A(None, x=random.randint(0, 10))
    obj.save()


button_send.bind('click', send_data)



