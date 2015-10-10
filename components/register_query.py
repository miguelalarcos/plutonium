registered_queries = {}


def register(Q):
    registered_queries[Q.__name__] = Q
    return Q


