import sys
sys.path.insert(0, 'http://localhost:8888/components')
import random
print('Iniciando aplicación::', random.random())

from components.main.init import init

init()

from browser import window
jq = window.jQuery.noConflict(True)

from components.main.controller import Controller

key = [('x', 'desc')]
filter = ('my_filter', {'x': 5, 'y': 10})
Controller('MyController', key, filter)


