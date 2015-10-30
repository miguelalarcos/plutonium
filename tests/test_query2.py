import sys
import datetime

sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
browser_mock = Mock()
sys.modules['browser'] = browser_mock

from lxml.html import InputElement
from components.main.reactive import Model, reactive, Reactive
#from components.main.page import parse, PageController
from components.main.query import Query, parse
import components.main.query
from pyquery import PyQuery


class ExtendedPyQuery(PyQuery):
    _data = {}
    _reactivity = {}
    _query = {}
    _click = {}
    _keyup = {}

    def keyup(self, method=None, event=None):
        if method:
            ExtendedPyQuery._keyup[self.attr('id')] = method
        else:
            ExtendedPyQuery._keyup[self.attr('id')](event)

    def click(self, method=None):
        if method:
            ExtendedPyQuery._click[self.attr('id')] = method
        else:
            ExtendedPyQuery._click[self.attr('id')]()

    def data(self, key, data=None):
        if key == 'reactivity':
            if data is None:
                return ExtendedPyQuery._reactivity.get(self.attr('id'))
            ExtendedPyQuery._reactivity[self.attr('id')] = data
        else:
            if data is None:
                return ExtendedPyQuery._query.get(self.attr('id'))
            ExtendedPyQuery._query[self.attr('id')] = data

    @staticmethod
    def contains(document, node):
        node = jq(node)
        id_ = node.attr('id') or 'None'
        if len(document.find('#'+id_)):
            return True
        rid = node.attr('reactive_id') or 'None'
        if len(document.find("[reactive_id='" + rid + "']")):
            return True
        return False

    def unbind(self):
        pass

jq = ExtendedPyQuery
components.main.query.jq = jq


class Root(Reactive):
    reactives = ['color']


root = Root(color='rojo')


class Coche(Reactive):
    reactives = ['matricula']


class Conductor(Reactive):
    reactives = ['apellido']


def test_0():
    html = """\
    <div>
        <div id='0' each="coches" param_color>
            <div id='1' r>{matricula}</div>
            <div id='2' each="conductores" param_matricula>
                <div id='3' r>{apellido}</div>
            </div>
        </div>
    </div>
    """
    node = jq(html)
    parse(node, root)
    #print(node)
    q = Query.queries["coches[('color', 'rojo')]"]
    q.append(Coche(matricula='ABC-10'))
    #print(node)
    q = Query.queries["conductores[('matricula', 'ABC-10')]"]
    q.append(Conductor(apellido='Alarcos'))
    print(node)
    print('root a color azul------')
    root.color = 'azul'
    print(node)
    assert False