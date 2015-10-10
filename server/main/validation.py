import server.main.load_models
from components.main.reactive import registered_models


def validate(raw):
    raw = raw.copy()
    collection = raw.pop('__collection__')
    klass = registered_models[collection]
    model = klass(**raw)
    return model.validate()
