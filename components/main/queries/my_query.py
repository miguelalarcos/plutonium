from components.main.query import Query
from components.register_query import register

@register
class MyQuery(Query):
    collection = 'A'

    def query(self):
        return {'x': {'$gte': self.a, '$lte': self.b}}
