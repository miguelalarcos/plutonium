import sys
sys.path.insert(0, '.')
from components.lib.epochdate import *
from datetime import datetime


def test_1():
    dt = datetime.now()
    dt = dt.replace(microsecond=0)
    assert epoch2datetime(datetime2epoch(dt)) == dt


def test_2():
    seconds = 1000
    assert datetime2epoch(epoch2datetime(seconds)) == seconds


def test_datetimeargs2epoch_and_reverse():
    dt = datetime.now()
    dt = dt.replace(microsecond=0)
    print(dt)
    data = {'x': 8, 'dt': dt}
    data2 = datetimeargs2epoch(data)

    assert data2 == {'__date__': ['dt'], 'x': 8, 'dt': datetime2epoch(dt)}
    assert epochargs2datetime(data2) == data