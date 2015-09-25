def index_by_id(models, id):
    index = None
    for item in models:
        if item.__getitem__:
            v = item['id']
        else:
            v = getattr(item, 'id')
        if v == id:
            if index is None:
                index = 0
            break
        if index is None:
            index = 0
        index += 1
    return index


def compare(a, b, key, order=1):
    if order == 'asc':
        order = 1
    if order == 'desc':
        order = -1
    if a.__getitem__:
        v_a = a[key]
        v_b = b[key]
    else:
        v_a = getattr(a, key)
        v_b = getattr(b, key)
    if v_a == v_b:
        return 0
    if v_a > v_b:
        if order == -1:
            return 1
        else:
            return -1
    if order == -1:
        return -1
    else:
        return 1


def index_in_list(models, key, model):
    if len(models) == 0:
        return 0

    index = 0

    keys = key[:]
    key, order = keys.pop(0)
    flag = False
    for item in models:
        while True:
            ret = compare(model, item, key, order)
            if ret == 1:
                flag = True
                break
            if ret == 0:
                if len(keys):
                    key, order = keys.pop(0)
                else:
                    flag = True
                    break
            else:
                break
        if flag:
            break
        index += 1
    return index
