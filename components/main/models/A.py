from components.main.reactive import Model, register


@register
class A(Model):
    def bool(self):
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



