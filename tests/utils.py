from bs4 import BeautifulSoup
from mock import Mock, MagicMock, call

class Attribute(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class Node(object):
    def __init__(self, html, parent=None):
        self.parent = parent
        self._html = html
        self.soup = BeautifulSoup(html, 'html.parser').div or BeautifulSoup(html, 'html.parser').span
        self.attributes = []
        for k, v in self.soup.attrs.items():
            self.attributes.append(Attribute(k, v))
        self._children = [Node(str(x), self) for x in self.soup.children if x.name in ('div', 'span')]
        self._data = None

    def __getitem__(self, item):
        return self

    def data(self, key, value=None):
        if value:
            self._data = value
        else:
            return self._data


    def find(self, attr):
        if attr == '[r]':
            return [x for x in self._children if x.attr('r')]
            #return [Node(str(x), self) for x in self.soup.find_all() if x.name in ('div', 'span') and x.has_attr('r')]
            #return self.soup.find_all(r="")
        return []

    def remove(self):
        self.parent.soup.clear()
        self.parent._children = []

    def first(self):
        try:
            return self._children[0]
        except IndexError:
            return None

    def append(self, nodes):
        node = nodes[0]
        self._children.append(node)
        node = BeautifulSoup(node._html, 'html.parser').div or BeautifulSoup(node._html, 'html.parser').span
        self.soup.append(node)

    def html(self, value=None):
        if value is None:
            return self._html
        self._html = value

    def children(self, reactive_id=None):
        if reactive_id:
            return Mock()
        return self._children
        #return [Node(str(x), self) for x in self.soup.children if x.name in ('div', 'span')]

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
                    self.soup.attrs[attr] = value

    def outerHTML(self):
        return self._html

    def removeAttr(self, attr):
        self.attributes = [x for x in self.attributes if x.name != attr]
        if attr in self.soup.attrs:
            del self.soup.attrs[attr]

    def click(self, method=None):
        if method is not None:
            self._click = method
        else:
            return self._click()
