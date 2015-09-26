#from components.main.filter_ import filters

filters = {}


def filter(collection):
    def helper1(func):
        def helper2(**kw):
            ret = func(**kw)
            ret.update({'__collection__': collection})
            return ret
        filters[func.__name__] = helper2
        return helper2
    return helper1

class Filter(object):
    def __init__(self, item):
        self.name = item.pop('__filter__')
        self.stop = item.pop('__stop__', None)
        self.raw_filter = item.copy()
        self.full_name = str([self.name] + sorted(self.raw_filter.items()))
        self.key = item.pop('__key__', None)
        self.limit = item.pop('__limit__', None)
        self.collection = item.pop('__collection__')
        self.skip = item.pop('__skip__', 0)
        self.filter = filters[self.name](**item)

    def pass_filter(self, model):
        print('model en pass_filter', model)
        if '__deleted__' in model.keys():
            return False
        for key, value in self.filter.items():
            if key == '__collection__':
                continue
            v = model.get(key)
            if v is None:
                return False
            if type(value) == int or type(value) == str:
                if v != value:
                    return False
            else:
                for op, val in value.items():
                    if op == '$gt':
                        if v <= val:
                            return False
                    elif op == '$lt':
                        if v >= val:
                            return False
                    elif op == '$gte':
                        if v < val:
                            return False
                    elif op == '$lte':
                        if v > val:
                            return False
        return True


def pass_filter(filter, model):
    print('model en pass_filter', model)
    if '__deleted__' in model.keys():
        return False
    for key, value in filter.items():
        if key == '__collection__':
            continue
        v = model.get(key)
        if v is None:
            return False
        if type(value) == int or type(value) == str:
            if v != value:
                return False
        else:
            for op, val in value.items():
                if op == '$gt':
                    if v <= val:
                        return False
                elif op == '$lt':
                    if v >= val:
                        return False
                elif op == '$gte':
                    if v < val:
                        return False
                elif op == '$lte':
                    if v > val:
                        return False
    return True

