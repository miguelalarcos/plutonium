from datetime import datetime


def datetime2epoch(dt):
    epoch = datetime.utcfromtimestamp(0)
    return (dt-epoch).total_seconds()


def epoch2datetime(ep):
    return datetime.utcfromtimestamp(ep)


def datetimeargs2epoch(data):
    data = data.copy()
    ret = []
    if '__date__' in data.keys():
        del data['__date__']
    for k, v in data.items():
        if type(v) == datetime:
            ret.append(k)
            data[k] = datetime2epoch(v)
    if len(ret) > 0:
        data['__date__'] = ret
    return data


def epochargs2datetime(data):
    data = data.copy()
    if '__date__' in data.keys():
        for k in data['__date__']:
            data[k] = epoch2datetime(data[k])
        del data['__date__']
    return data