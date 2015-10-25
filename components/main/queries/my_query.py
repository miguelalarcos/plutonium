from components.main.page import Query, register

@register
class MyQuery(Query):
    collection = 'A'

    def query(self):
        return {'x': {'$gte': self.a, '$lte': self.b}}
