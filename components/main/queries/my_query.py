from components.main.page import Query
from components.main.queries import register_query

@register_query
class MyQuery(Query):
    _collection = 'A'

    def query(self):
        return {'x': {'$gte': self.a, '$lte': self.b}}
