queries = {}

def register_query(Q):
    queries[Q.__name__] = Q
