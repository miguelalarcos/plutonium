from tornado import ioloop, gen
from tornado.queues import Queue
import motor
from components.lib.epochdate import datetimeargs2epoch
import json
from server.main.client import Client
from server.main.DB import DB
from server.main.validation import validate
from server.main.task import registered_tasks
from components.lib.filter_mongo import pass_filter

db = motor.MotorClient().test_database

q_mongo = Queue()
q_send = Queue()

@gen.coroutine
def sender():
    while True:
        print('yield: q_send.get()')
        items = yield q_send.get()
        if type(items) != list:
            items = [items]
        for item in items:
            client = item[0]
            model = item[1]
            model = datetimeargs2epoch(model)
            print('yield: client.write', json.dumps(model))
            client.write_message(json.dumps(model))
        q_send.task_done()


@gen.coroutine
def handle_filter(item):
    client_socket = item.pop('__client__')
    client = Client.clients[client_socket]

    name = item.pop('__filter__')
    filt = client.add_filter(name, item)
    collection = filt.pop('__collection__')

    ret = yield db[collection].find(filt)
    if ret:
        ret = [(client.socket, r) for r in ret]
        yield q_send.put(ret)
    raise gen.Return('handle_filter done')


@gen.coroutine
def mongo_consumer():

    while True:
        print('yield: q_mongo.get()')
        item = yield q_mongo.get()
        print('item from queue', item)

        if '__filter__' in item.keys():
            yield handle_filter(item)
        elif '__RPC__' in item.keys():
            name = item.pop('__RPC__')
            task = registered_tasks[name]
            ioloop.IOLoop.current().spawn_callback(task, db=DB(db), queue=q_mongo, **item)
        else:
            collection = item['__collection__']
            model = item

            new = False
            deleted = False
            print('future')
            future = db[collection].find_one({'_id': model['id']})
            print('buscamos model before')
            model_before = yield future
            print('model before', model_before)
            if model_before is None:
                model_id = model.copy()
                model_id['_id'] = model_id['id']
                del model_id['id']
                print('yield insert')
                if validate(model):
                    yield db[collection].insert(model_id)
                else:
                    continue
                new = True
            elif '__deleted__' in model.keys():
                deleted = True
                print('yield remove')
                yield db[collection].remove({'_id': model['id']})
            else:
                model_copy = model.copy()
                del model_copy['id']
                del model_copy['__collection__']
                print('yield update')
                model2validate = model_before.copy()
                model2validate.update(model)
                if validate(model2validate):
                    yield db[collection].update({'_id': model['id']}, {"$set": model_copy})
                else:
                    continue

            for client in Client.clients.values():
                for filt in client.filters.values():
                    print('filter:', filt)
                    if filt['__collection__'] != collection:
                        continue
                    before = (not new) and pass_filter(filt, model_before)
                    print('before:', before)

                    if not before and not deleted:
                        model_after = model_before.copy()
                        model_after.update(model)
                        after = pass_filter(filt, model_after)
                        print('after:', after)
                        if after:
                            print('send', client.socket, model)
                            yield q_send.put((client.socket, model))
                            break
                    else:
                        print('send', client.socket, model)
                        yield q_send.put((client.socket, model))
                        break
        q_mongo.task_done()


