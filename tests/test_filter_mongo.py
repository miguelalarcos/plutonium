from components.lib.filter_mongo import pass_filter

filters = {}
filters['0'] = lambda a, b: {'__collection__': 'A', 'x': {"$gt": a, "$lt": b}}
filters['2'] = lambda a, b: {'__collection__': 'A', 'x': {"$gte": a, "$lte": b}}
filters['1'] = lambda a, b: {'__collection__': 'A', 'x': {"$gt": a, "$lt": b}, 'y': {"$gt": a, "$lt": b}}


def test_1():
    filter = filters['0'](5, 10)

    assert pass_filter(filter, {'x': 9})
    assert not pass_filter(filter, {'x': 0})
    assert not pass_filter(filter, {'x': 5})
    assert not pass_filter(filter, {'x': 10})
    assert not pass_filter(filter, {'x': 11})


def test_3():
    filter = filters['2'](5, 10)

    assert pass_filter(filter, {'x': 9})
    assert not pass_filter(filter, {'x': 0})
    assert pass_filter(filter, {'x': 5})
    assert pass_filter(filter, {'x': 10})
    assert not pass_filter(filter, {'x': 11})


def test_2():
    filter = filters['1'](5, 10)

    assert pass_filter(filter, {'x': 9, 'y': 9})
    assert not pass_filter(filter, {'x': 9, 'y': 0})


