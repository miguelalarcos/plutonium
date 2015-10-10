from components.main.reactive import Model
from components.register_model import register


@register
class A(Model):
    def flag(self):
        return self.x == 9

    def minus(self):
        print('llego a minus', self.id)
        self.x -= 1
        self.save()

    def plus(self):
        print('llego a plus', self.id)
        self.x += 1
        self.save()

    def validate_x(self):
        return type(self.x) == int and self.x > 0

    def red_if_negative(self):
        if self.x < 0:
            return 'red'
        return ''



