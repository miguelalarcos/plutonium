registered_queries = {}


def register_query(Q):
    registered_queries[Q.__name__] = Q
    return Q

import components.main.queries.my_query
