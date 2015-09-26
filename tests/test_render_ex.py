import sys
sys.path.insert(0, '.')
from mock import Mock, MagicMock, call
sys.modules['browser'] = Mock()

from components.main.controller import render_ex
from bs4 import BeautifulSoup
from components.main.reactive import Model


class A(Model):
    objects = {}

    def __init__(self, id, **kw):
        super(A, self).__init__(id, **kw)


class Attribute(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class Node(object):
    def __init__(self, html):
        self._html = html
        self.soup = BeautifulSoup(html, 'html.parser').div or BeautifulSoup(html, 'html.parser').span
        self.attributes = []
        for k, v in self.soup.attrs.items():
            self.attributes.append(Attribute(k, v))

    def __getitem__(self, item):
        return self

    def html(self, value=None):
        if value is None:
            return self._html
        self._html = value

    def children(self):
        return [Node(str(x)) for x in self.soup.children if x.name in ('div', 'span')]

    def attr(self, attr, value=None):
        if value is None:
            try:
                return self.soup.attrs[attr]
            except KeyError:
                return None
        else:
            for item in self.attributes:
                if item.name == attr:
                    item.value = value

    def outerHTML(self):
        return self._html


def test_1():
    node = Node("<div if='{z}'><span r>{x}</span><span r>{y}</span></div")
    m = A(id=None, x=8, y=9, z=True)
    render_ex(node, m)
    m.y=900
    assert False