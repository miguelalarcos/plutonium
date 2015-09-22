import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
sys.modules['browser'] = Mock()

from components.main.controller import render, makeDIV
from components.main.reactive import Model, consume, execute, reactive_first
from components.main import controller

filters = {}
controller.filters = filters
filters['0'] = lambda x, y: {'__collection__': 'A', 'x': {"$gt": x, "$lt": y}}

class A(Model):
    objects = {}


def test_1():
    node1 = Mock()
    node2 = Mock()
    jq = MagicMock()
    node = MagicMock()
    node.find().__iter__.return_value = [node1, node2]
    jq.side_effect = [node, node1, node2]

    controller.jq = jq

    model = A(id=None, x=8, y=9)

    node1.html.return_value = '<span r>{x}</span>'
    node2.html.return_value = '<span r>{y}</span>'

    makeDIV('0', model, render, '<span r>{x}</span> <span r>{y}</span>')
    assert node.html.called
    assert call('<span r>8</span>') in node1.html.mock_calls
    assert call('<span r>9</span>') in node2.html.mock_calls
    assert model._dirty == set(['x', 'y'])

    model.x = 800
    assert len(execute) == 1
    consume()
    assert call('<span r>800</span>') in node1.html.mock_calls


def test_render_model():
    jq = MagicMock()
    controller.jq = jq
    node = jq()
    node.html.return_value = '<span r>{x}</span> <span r>{y}</span>'

    c = controller.Controller(name='', key=[('x', 'desc'), ('y', 'desc')], filter=('0', {'x': 5, 'y': 10}))
    m = A(id=None, x=8, y=9)
    c.models = []

    cfm = controller.FirstModelController('', c)

    c.new(m)
    consume()
    assert call('<span r>8</span> <span r>9</span>') in node.html.mock_calls
    #assert False


