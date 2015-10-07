from bs4 import BeautifulSoup
from mock import Mock, MagicMock, call

class Attribute(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return self.name + ':' + self.value


class Children(list):
    def first(self):
        if len(self) > 0:
            return self[0]
        #else:
        #    return Node('<div></div>')
    @property
    def length(self):
        return len(self)

    def before(self, node):
        pass

    def after(self, node):
        pass

    def remove(self):
        pass


class Node(object):
    def __init__(self, html, parent=None):
        self.parent = parent
        self._html = html
        self.soup = BeautifulSoup(html, 'html.parser').div or BeautifulSoup(html, 'html.parser').span

        self._inner_html = "".join([str(x) for x in self.soup.contents])

        self.attributes = []
        for k, v in self.soup.attrs.items():
            self.attributes.append(Attribute(k, v))
        self._children = Children([Node(str(x), self) for x in self.soup.children if x.name in ('div', 'span')])
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
            return [x for x in self._children if x.attr('r') == '']
        return []

    def remove(self):
        self.parent.soup.clear()
        self.parent._children = Children([])

    def first(self):
        return self

    def before(self, node):
        pass

    def unbind(self):
        pass

    def append(self, nodes):
        node = nodes[0]
        self._children.append(node)
        node = BeautifulSoup(node._html, 'html.parser').div or BeautifulSoup(node._html, 'html.parser').span
        self.soup.append(node)

    def html(self, value=None):
        if value is None:
            #return self._html
            return self._inner_html
        self._inner_html = value
        self.soup.string = value

        #self._html = value

    def children(self, *args):
        return self._children

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

    @property
    def outerHTML(self):
        return str(self.soup)
        print('>', self.html(), self.soup)
        dct = {}
        for attr in self.attributes:
            dct[attr.name] = attr.value
        return str(self.soup).format(**dct)

    def removeAttr(self, attr):
        self.attributes = [x for x in self.attributes if x.name != attr]
        if attr in self.soup.attrs:
            del self.soup.attrs[attr]

    def click(self, method=None):
        if method is not None:
            self._click = method
        else:
            return self._click()

    def removeClass(self, klass):
        if klass in self.soup.get('class', []):
            self.soup.get('class').remove(klass)

    def hasClass(self, name):
        if self.soup.get('class') is None:
            return False
        return name in self.soup.get('class')

    def __repr__(self):
        return str(self.soup)