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

from components.main.reactive import reactive
from components.main.page import Controller
from components.main.queries.my_query import MyQuery



class MyController(Controller):
    def __init__(self, id, *args, **kwargs):
        super().__init__(id, *args, **kwargs)

        @reactive
        def f():
            q = MyQuery(id='0', sort=(('x', 1),), skip=0, limit=1, a=self.a, b=self.b)
            self.subscribe(q)

    def x(self):
        return False

init(MyController(id='my controller', a=0, b=10))

"""
button_send = jq('#button')
sent_initial_data = False

def send_data():
    global sent_initial_data
    if not sent_initial_data:
        BaseController.subscribe_all()
        sent_initial_data = True


button_send.bind('click', send_data)
"""


