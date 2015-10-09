class Client(object):
    clients = {}

    def __init__(self, socket):
        self.socket = socket
        self.queries = {}
        Client.clients[socket] = self

    def add_query(self, query):
        if query.stop:
            del self.queries[query.stop]

        self.queries[query.full_name] = query

    @classmethod
    def remove_client(cls, client):
        del cls.clients[client.socket]
