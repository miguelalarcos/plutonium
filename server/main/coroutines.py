from tornado import ioloop, gen
from tornado.queues import Queue
import motor
from components.lib.epochdate import datetimeargs2epoch
import json
from server.main.client import Client
from server.main.DB import DB
from server.main.validation import validate
from server.main.task import registered_tasks
from components.lib.utils import index_by_id, index_in_list


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
def do_find(filt):
    cursor = db[filt.collection].find(filt.filter)
    if filt.key:
        cursor.sort(filt.key)
    if filt.limit:
        cursor.limit(filt.limit)
    ret = []
    while (yield cursor.fetch_next):
        document = cursor.next_object()
        document['__collection__'] = filt.collection
        document['id'] = document['_id']
        del document['_id']
        ret.append(document)
    return ret


@gen.coroutine
def handle_filter(item):
    client_socket = item.pop('__client__')
    client = Client.clients[client_socket]

    name = item.pop('__filter__')
    filt = client.add_filter(name, item)
    #collection = filt.collection   # pop('__collection__')

    #cursor = db[collection].find(filt.filter)
    #if filt.key:
    #    cursor.sort(filt.key)
    #if filt.limit:
    #    cursor.limit(filt.limit)
    #ret = []
    #while (yield cursor.fetch_next):
    #    document = cursor.next_object()
    #    document['__collection__'] = collection
    #    document['id'] = document['_id']
    #    del document['_id']
    #    ret.append(document)
    ret = yield do_find(filt)
    if len(ret) > 0:
        ret = [(client.socket, r) for r in ret]
        yield q_send.put(ret)

    return


def handle_rpc(item):
    name = item.pop('__RPC__')
    task = registered_tasks[name]
    ioloop.IOLoop.current().spawn_callback(task, db=DB(db), queue=q_mongo, **item)


@gen.coroutine
def handle_collection(item):
    collection = item['__collection__']
    del item['__client__']
    model = item

    new = False
    deleted = False
    print('buscamos model before')
    model_before = yield db[collection].find_one({'_id': model['id']})
    print('model before', model_before)
    if model_before is None:
        model_id = model.copy()
        model_id['_id'] = model_id['id']
        del model_id['id']
        del model_id['__collection__']

        if validate(model):
            print('yield insert', model_id)
            yield db[collection].insert(model_id)
        else:
            print('retornamos sin hacer insert')
            return
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
            return
    yield broadcast(collection, new, model_before, deleted, model)


@gen.coroutine
def broadcast(collection, new, model_before, deleted, model):
    print('len: ', len(Client.clients))
    for client in Client.clients.values():
        print('filter of client:', client.filters)
        for filt in client.filters.values():
            print('filt', filt)
            break_flag = False
            position_after = None
            last_doc = None

            if filt.collection != collection:
                print('continue')
                continue
            if filt.limit:
                if model_before:
                    docs = yield do_find(filt)
                    last_doc = docs[-1]
                    pos = index_by_id(docs, model_before['id'])
                    position_after = pos
                    if pos is not None and pos < filt.limit:
                        del docs[pos]
                    pos = index_in_list(docs, filt.key, model_before)
                    if pos >= filt.limit:
                        before = False
                    else:
                        before = True # and filt.pass_filter(model_before)
                else:
                    before = False
            else:
                before = (not new) and filt.pass_filter(model_before)

            print('before', before)
            after = None
            if not before and not deleted:
                if model_before is None:    # repasar esto
                    model_after = model.copy()
                else:
                    model_after = model_before.copy()
                    model_after.update(model)

                if filt.limit:
                    after = position_after < filt.limit # and filt.pass_filter(model_after)
                else:
                    after = filt.pass_filter(model_after)
                print('after:', after)
                if after:
                    print('send(1)', client.socket, model)
                    yield q_send.put((client.socket, model))
                    break_flag = True
            else:
                print('send(2)', client.socket, model)
                yield q_send.put((client.socket, model))
                break_flag = True

            if before and filt.limit and position_after >= filt.limit and last_doc and last_doc['id'] != model['id']:
                print('send(3)', client.socket, last_doc)
                yield q_send.put((client.socket, last_doc))
            if break_flag:
                print('             break')
                break

@gen.coroutine
def mongo_consumer():
    while True:
        item = yield q_mongo.get()
        print('item from queue', item)

        if '__filter__' in item.keys():
            yield handle_filter(item)
        elif '__RPC__' in item.keys():
            handle_rpc(item)
        else:
            yield handle_collection(item)

        q_mongo.task_done()


