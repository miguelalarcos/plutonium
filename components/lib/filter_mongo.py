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

