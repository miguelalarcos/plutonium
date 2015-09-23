from tornado import gen


class DB(object):
    def __init__(self, db):
        self.db = db

    def __getitem__(self, item):
        self.collection = item
        return self

    @gen.coroutine
    def find(self, parameters):
        items = yield self.db[self.collection].find(parameters) #esto no funciona. ver yield para find hecho en otro fichero
        ret = []
        for item in items:
            item.update({'__collection__': self.collection})
            ret.append(item)
        raise gen.Return(ret)

    @gen.coroutine
    def find_one(self, id):
        item = yield self.db[self.collection].find_one({'_id': id})
        item.update({'__collection__': self.collection})
        return item




