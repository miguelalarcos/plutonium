from tornado import ioloop, gen
from tornado.queues import Queue
import motor
from components.lib.epochdate import datetimeargs2epoch
import json
from server.main.client import Client
from server.main.DB import DB
from server.main.validation import validate
from server.main.task import registered_tasks
#from components.main.page import Query
#from components.lib.utils import index_by_id
import components.load_queries
from components.register_query import registered_queries

db = motor.MotorClient().test_database

q_mongo = Queue()
q_send = Queue()

@gen.coroutine
def sender():
    while True:
        items = yield q_send.get()
        if type(items) != list:
            items = [items]
        for item in items:
            client = item[0]
            model = item[1]
            model = datetimeargs2epoch(model)
            client.write_message(json.dumps(model))
        q_send.task_done()


@gen.coroutine
def do_find(query, projection=None): #

    if projection:
        cursor = db[query.collection].find(query.query(), projection)
    else:
        cursor = db[query.collection].find(query.query())
    if query.sort:
        cursor.sort(query.sort)
    cursor.skip(query.skip)
    if query.limit:
        cursor.limit(query.limit)

    ret = yield cursor.to_list(length=query.limit)
    for document in ret:
        document['__collection__'] = query.collection
        document['__query__'] = query.full_name
        document['id'] = document['_id']
        del document['_id']
    return ret


@gen.coroutine
def handle_query(item):
    client_socket = item.pop('__client__')
    client = Client.clients[client_socket]
    sort = item.pop('__sort__')
    sort = tuple([tuple(x) for x in sort])
    skip = item.pop('__skip__')
    limit = item.pop('__limit__')
    stop = item.pop('__stop__', None)
    name = item.pop('__query__')
    query = registered_queries[name](id=None, sort=sort, skip=skip, limit=limit, stop=stop, **item)
    client.add_query(query)

    ret = yield do_find(query)
    if len(ret) > 0:
        for r in ret:
            r['__new__'] = True
            r['__position__'] = 'append'
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
    for client in Client.clients.values():
        for query in client.queries.values():
            ret = yield do_find(query, {'_id': 1})
            query.before = [x['id'] for x in ret]

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
        for query in client.queries.values():
            if query.collection != collection:
                continue
            after = yield do_find(query, {'_id': 1})
            after = [x['id'] for x in after]
            before = query.before
            to_send = yield broadcast_helper(item, before, after, query.limit, collection )
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
                if item['id'] in before:
                    to_send['__out__'] = item['id']
                break
    if not to_send and item['id'] in before:
        to_send = item
        to_send['__out__'] = item['id']

    if to_send:
        if to_send['id'] in after:
            index = after.index(to_send['id'])
            if index == 0:
                if len(after) == 1:
                    position = 'append'
                elif len(after) > 1:
                    position = 'before'
            else:
                position = after[index-1]
            to_send['__position__'] = (position, index)

        if to_send['id'] not in before:
            to_send['__new__'] = True

    return to_send


@gen.coroutine
def mongo_consumer():
    while True:
        item = yield q_mongo.get()
        print('item from queue', item)

        if '__query__' in item.keys():
            yield handle_query(item)
        elif '__RPC__' in item.keys():
            handle_rpc(item)
        else:
            yield handle_collection(item)

        q_mongo.task_done()


