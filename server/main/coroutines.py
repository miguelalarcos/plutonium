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
from components.lib.filter_mongo import Filter


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
def do_find(filt, projection=None): #

    if projection:
        cursor = db[filt.collection].find(filt.filter, projection)
    else:
        cursor = db[filt.collection].find(filt.filter)
    if filt.key:
        cursor.sort(filt.key)
    cursor.skip(filt.skip)
    if filt.limit:
        cursor.limit(filt.limit)

    ret = yield cursor.to_list(length=filt.limit)
    for document in ret:
        document['__collection__'] = filt.collection
        document['__filter__'] = filt.full_name
        document['id'] = document['_id']
        del document['_id']
    print('do find', ret)
    return ret


@gen.coroutine
def handle_filter(item):
    client_socket = item.pop('__client__')
    client = Client.clients[client_socket]

    filt = Filter(item)
    client.add_filter(filt)

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
    print('llego')
    for client in Client.clients.values():
        print('client.filters', client.filters)
        for filt in client.filters.values():
            ret = yield do_find(filt, {'_id': 1})
            filt.before = [x['id'] for x in ret]
    model_before = yield db[collection].find_one({'_id': item['id']})
    if model_before is None:
        model_id = item.copy()
        model_id['_id'] = model_id['id']
        del model_id['id']
        del model_id['__collection__']

        if validate(item):
            yield db[collection].insert(model_id)
        else:
            return
    elif '__deleted__' in item.keys():
        yield db[collection].remove({'_id': item['id']})
    else:
        model_copy = item.copy()
        del model_copy['id']
        del model_copy['__collection__']
        model2validate = model_before.copy()
        model2validate.update(item)
        if validate(model2validate):
            yield db[collection].update({'_id': item['id']}, {"$set": model_copy})
        else:
            return

    yield broadcast(item)


@gen.coroutine
def do_find_one(collection, id):
    doc = yield db[collection].find_one({'_id': id})
    if doc:
        doc['__collection__'] = collection
        doc['id'] = doc['_id']
        del doc['_id']
        return doc
    return None


@gen.coroutine
def broadcast(item):
    collection = item['__collection__']
    for client in Client.clients.values():
        for filt in client.filters.values():
            if filt.collection != collection:
                continue
            after = yield do_find(filt, {'_id': 1})
            after = [x['id'] for x in after]
            before = filt.before
            to_send = yield broadcast_helper(item, before, after, filt.limit, collection )
            if to_send:
                yield q_send.put((client.socket, to_send))


@gen.coroutine
def broadcast_helper(item, before, after, limit, collection):
    to_send = None
    if item['id'] in after:
        to_send = item
        if len(before) == limit and item['id'] not in before:
            if after[0] != before[0]:
                to_send['__out__'] = before[0]
            else:
                to_send['__out__'] = before[-1]
    else:
        tupla = []
        if len(after) == 1:
            tupla = (0, )
        elif len(after) > 1:
            tupla = (0, -1)
        for index in tupla:
            id = after[index]
            if id not in before:
                doc = yield do_find_one(collection, id)
                to_send = doc
                to_send['__out__'] = item['id']
                break
    if not to_send and item['id'] in before:
        to_send = item
        to_send['__out__'] = item['id']

    if to_send:
        if to_send['id'] not in before:
            to_send['__new__'] = True

    return to_send


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


