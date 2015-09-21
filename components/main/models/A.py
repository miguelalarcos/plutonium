print('M(1)')
from components.main.reactive import Model, register
print('M(2)')

@register
class A(Model):
    def validate_x(self):
        return type(self.x) == int and self.x > 0



