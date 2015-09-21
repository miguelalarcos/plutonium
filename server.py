from tornado import web, ioloop


class MainHandler(web.RequestHandler):
    def get(self):
        self.render("index.html")

app = web.Application([
    (r"/", MainHandler),
    (r"/main/(.*)", web.StaticFileHandler, {"path": "/home/miguel/development/brython/final"}),
    (r"/components/(.*)", web.StaticFileHandler, {"path": "/home/miguel/development/brython/final/components"}),
])


if __name__ == '__main__':
    app.listen(8888)
    ioloop.IOLoop.instance().start()




