from components.main.reactive import Model, register


@register
class A(Model):
    def validate_x(self):
        return type(self.x) == int and x > 100



