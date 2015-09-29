from components.main.reactive import Model, register


@register
class A(Model):
    def bool(self):
        return self.x == 9

    def minus(self):
        self.x -= 1
        print('llego a minus', self._dirty)
        self.save()

    def plus(self):
        self.x += 1
        self.save()

    def validate_x(self):
        return type(self.x) == int and self.x > 0



