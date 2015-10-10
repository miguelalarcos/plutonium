from browser import window
import javascript

from components.lib.epochdate import epochargs2datetime

import json
from components.main.reactive import Model, execute_block
import components.load_models
from components.register_model import registered_models
from components.main.page import Controller

WebSocket = javascript.JSConstructor(window.WebSocket)

jq = window.jq


def set_page_controller(c):
    global page_controller
    page_controller = c


def on_message(evt):
    try:
        result = evt.data
        print('raw', result)
        data = json.loads(result)
        data = epochargs2datetime(data)
        raw = data.copy()
        collection = data.pop('__collection__')
        filter_name = data.pop('__query__')
        position = data.pop('__position__', None)
        out = data.pop('__out__', None)
        new = data.pop('__new__', None)

        klass = registered_models[collection]
        print('buscamos si ya tenemos el objeto con id', data['id'])
        try:
            model = klass.objects[data['id']]
            print('encontrado')
            with execute_block():
                for k, v in data.items():
                    if k in ('id', '__deleted__'): # es necesario deleted??
                        continue
                    setattr(model, '_'+k, v)
        except KeyError:
            print('nuevo')
            data_ = {}
            for k, v in data.items():
                if not k.startswith('_') and k != 'id':
                    data_['_'+k] = v
                else:
                    data_[k] = v
            model = klass(**data_)

        print('test all controllers')
        page_controller.test(model, raw)
        #if all(r):
        #    del klass.objects[model.id]
    except Exception as e:
        print ('******************** error', e)


def init(main):
    print('iniciando socket')
    ws = WebSocket("ws://127.0.0.1:8888/ws")
    Model.ws = ws
    Controller.ws = ws

    ws.bind('message', on_message)
    ws.onopen = main

