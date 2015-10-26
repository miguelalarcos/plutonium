import json

registered_queries = {}


def register(Q):
    registered_queries[Q.__name__] = Q
    return Q


class Query(Reactive):
    def __init__(self, full_name, name, sort, skip, limit, **kwargs):
        super().__init__(**kwargs)
        self.full_name = full_name
        self.name = name
        self.sort = sort
        self.skip = skip
        self.limit = limit
        self.kw = kwargs
        self.stop = None
        self.models = []
        self.node = None

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