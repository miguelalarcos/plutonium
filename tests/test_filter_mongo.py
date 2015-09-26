from components.lib.filter_mongo import Filter, filter

#filters = {}
#filters['0'] = lambda a, b: {'__collection__': 'A', 'x': {"$gt": a, "$lt": b}}
#filters['2'] = lambda a, b: {'__collection__': 'A', 'x': {"$gte": a, "$lte": b}}
#filters['1'] = lambda a, b: {'__collection__': 'A', 'x': {"$gt": a, "$lt": b}, 'y': {"$gt": a, "$lt": b}}

@filter('A')
def filter_1(a, b):
    return {'x': {"$gt": a, "$lt": b}}

@filter('A')
def filter_2(a, b):
    return {'x': {"$gte": a, "$lte": b}}

@filter('A')
def filter_3(a, b):
    return {'x': {"$gt": a, "$lt": b}, 'y': {"$gt": a, "$lt": b}}

filter_1_obj = Filter(collection='A', filter='filter_1', key=[('x', -1), ], limit=2, skip='0', a=5, b=10)
filter_2_obj = Filter(collection='A', filter='filter_2', key=[('x', -1), ], limit=2, skip='0', a=5, b=10)
filter_3_obj = Filter(collection='A', filter='filter_3', key=[('x', -1), ], limit=2, skip='0', a=5, b=10)


def test_1():
    assert filter_1_obj.pass_filter({'x': 9})
    assert not filter_1_obj.pass_filter({'x': 0})
    assert not filter_1_obj.pass_filter({'x': 5})
    assert not filter_1_obj.pass_filter({'x': 10})
    assert not filter_1_obj.pass_filter({'x': 11})


def test_3():
    assert filter_2_obj.pass_filter({'x': 9})
    assert not filter_2_obj.pass_filter({'x': 0})
    assert filter_2_obj.pass_filter({'x': 5})
    assert filter_2_obj.pass_filter({'x': 10})
    assert not filter_2_obj.pass_filter({'x': 11})


def test_2():
    assert filter_3_obj.pass_filter({'x': 9, 'y': 9})
    assert not filter_3_obj.pass_filter({'x': 9, 'y': 0})


