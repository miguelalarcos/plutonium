import sys
sys.path.insert(0, '.')
from components.main.reactive import reactive, Model, consume, execute, basic_reactive


class A(Model):
    objects = {}

    def __init__(self, id, **kw):
        super(A, self).__init__(id, **kw)

ret = None


def h(model, node, template):
    global ret
    ret = (model.x, model.y)


def test_1():
    m = A(id='0', x=0)

    m.y = 3
    assert execute == []
    reactive(m, h)

    m.x = 7
    m.x = 8
    m.y = 9

    #assert len(execute) == 1
    #consume()

    assert ret == (8, 9)
    assert len(m._dep) == 2

    m.y = 9
    assert execute == []
    assert m._dirty == set(['selected', 'x', 'y'])

    m._dirty = set()
    m._x = 900
    assert m._dirty == set()


def test_basic_reactive():
    m = A(id='0', x=0, y=0)
    ret = None

    def rf():
        nonlocal ret
        ret = m.x, m.y
    basic_reactive(rf)
    m.y = 8

    assert ret == (0, 8)

