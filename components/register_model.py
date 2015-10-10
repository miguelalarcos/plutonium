registered_models = {}


def register(M):
    M.objects = {}
    registered_models[M.__name__] = M
    return M




