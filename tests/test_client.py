import sys
sys.path.insert(0, '.')
from server.main.client import Client
import components.main.filters.my_filter

cl = Client('0')


def test_add_filter():
    filter = {'x': 5, 'y': 10}
    filter = cl.add_filter('my_filter', filter)
    assert filter == {'__collection__': 'A', 'x': {'$gt': 5, '$lt': 10}}
    assert list(cl.filters.keys())[0] == ('my_filter', ('x', 5), ('y', 10))

    filter = {'__stop__': {'x': 5, 'y': 10}, 'x': 6, 'y': 11}
    filter = cl.add_filter('my_filter', filter)
    assert filter == {'__collection__': 'A', 'x': {'$gt': 6, '$lt': 11}}
    assert list(cl.filters.keys())[0] == ('my_filter', ('x', 6), ('y', 11))
    assert len(cl.filters.keys()) == 1
