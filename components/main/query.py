import json


class Query(object):
    def __init__(self, id, sort, skip, limit, stop=None, **kw):
        self.id = id
        self.name = self.__class__.__name__
        self.full_name = str((self.__class__.__name__, tuple(sorted([('__collection__', self.collection),
                                                                     ('__sort__', sort), ('__skip__', skip)] +
                                                                    list(kw.items()) + [('__limit__', limit)]))))
        self.sort = sort
        self.skip = skip
        self.limit = limit
        for k,v in kw.items():
            setattr(self, k, v)
        self.models = []
        self.nodes = []
        self.stop = stop
        self.kw = kw

    def dumps(self):
        arg = {}
        arg['__query__'] = self.name
        arg['__sort__'] = self.sort
        arg['__skip__'] = self.skip
        arg['__limit__'] = self.limit
        if self.stop:
            arg['__stop__'] = self.stop
        for k, v in self.kw.items():
            arg[k] = v
        return json.dumps(arg)
