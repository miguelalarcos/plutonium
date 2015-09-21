from tornado import web, ioloop
import os

path = os.path.dirname(os.path.abspath(__file__))


class MainHandler(web.RequestHandler):
    def get(self):
        self.render("components/main/views/index.html")

app = web.Application([
    (r"/", MainHandler),
    (r"/main/(.*)", web.StaticFileHandler, {"path": path}),
    (r"/components/(.*)", web.StaticFileHandler, {"path": os.path.join(path, 'components')}),
])


if __name__ == '__main__':
    app.listen(8888)
    ioloop.IOLoop.instance().start()




