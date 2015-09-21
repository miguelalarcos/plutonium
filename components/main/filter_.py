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
