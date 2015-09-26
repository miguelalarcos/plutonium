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

    @classmethod
    def remove_client(cls, client):
        del cls.clients[client.socket]
