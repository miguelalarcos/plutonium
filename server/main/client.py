from components.main.filter_ import filters
from components.lib.filter_mongo import Filter


class Client(object):
    clients = {}

    def __init__(self, socket):
        self.socket = socket
        self.filters = {}
        Client.clients[socket] = self

    def add_filter(self, filter):
        if filter.stop:
            del self.filters[filter.stop]

        self.filters[filter.full_name] = filter

        #if '__stop__' in filter.keys():
        #    stop = filter.pop('__stop__')
        #    self.remove_filter(name, stop)

        #filt = Filter(filter)
        #name = [name] + sorted(filter.items())
        #self.filters[tuple(name)] = filt  # filt
        #return filt  #.copy()

    #def remove_filter(self, name, filter):
    #    name = [name] + sorted(filter.items())
    #    name = tuple(name)
    #    del self.filters[name]

    @classmethod
    def remove_client(cls, client):
        del cls.clients[client.socket]
