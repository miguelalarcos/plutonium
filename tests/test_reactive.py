import sys
sys.path.insert(0, '.')
from components.main.reactive import reactive, Model, execute, execute_block


class A(Model):
    objects = {}

    def __init__(self, id, **kw):
        super(A, self).__init__(id, **kw)

ret = None


def h(model):
    global ret
    ret = (model.x, model.y)


def test_basic_reactive():
    m = A(id='0', x=0)

    m.y = 3
    assert execute == []
    reactive(h, m)

    m.x = 7
    m.x = 8
    m.y = 9

    assert len(execute) == 0

    assert ret == (8, 9)
    assert len(m._dep) == 2

    m.y = 9
    assert execute == []
    assert m._dirty == set(['x', 'y'])

    m._dirty = set()
    m._x = 900
    assert m._dirty == set()


def test_context_manager():
    ret = None

    def f(m):
        nonlocal ret
        ret = m.x, m.y

    with execute_block():
        m = A(id='0', x=0, y=0)
        reactive(f, m)
        m.x = 1
        m.y = 1
        assert len(execute) == 1
    assert len(execute) == 0
    assert ret == (1, 1)
