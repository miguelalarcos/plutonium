from tornado import gen
registered_tasks = {}


def task(func):
    func = gen.coroutine(func)
    registered_tasks[func.__name__] = func
    return func

