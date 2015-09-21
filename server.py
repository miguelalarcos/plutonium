from tornado import web, ioloop, websocket, gen
import os
import json
from components.lib.epochdate import epochargs2datetime
from server.main.coroutines import mongo_consumer, sender, q_mongo
from server.main.client import Client

class MainHandler(web.RequestHandler):
    def get(self):
        self.render("components/main/views/index.html")


class SocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        Client(self)

    def close(self):
        Client.remove_client(self)

    @gen.coroutine
    def on_message(self, message):
        print('***', message)
        item = json.loads(message)
        item = epochargs2datetime(item)
        item['__client__'] = self
        print('yield: q_mongo.put()')
        yield q_mongo.put(item)


path = os.path.dirname(os.path.abspath(__file__))
app = web.Application([
    (r"/", MainHandler),
    (r'/ws', SocketHandler),
    (r"/main/(.*)", web.StaticFileHandler, {"path": path}),
    (r"/components/(.*)", web.StaticFileHandler, {"path": os.path.join(path, 'components')}),
])


if __name__ == '__main__':
    app.listen(8888)
    ioloop.IOLoop.current().spawn_callback(mongo_consumer)
    ioloop.IOLoop.current().spawn_callback(sender)
    ioloop.IOLoop.instance().start()




