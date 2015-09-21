from components.main.reactive import registered_models


def validate(raw):
    collection = raw.pop('__collection__')
    klass = registered_models[collection]
    model = klass(**raw)
    return model.validate()
