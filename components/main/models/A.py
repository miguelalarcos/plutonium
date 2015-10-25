from components.main.reactive import Model, register, reactive


@register
class A(Model):
    reactives = ['x', 'bflag', 'bminus']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        @reactive
        def r():
            self.bflag = self.x == 9

        @reactive
        def r():
            self.bminus = self.x != -1

    #def flag(self):
    #    return self.x == 9

    def minus(self):
        self.x -= 1
        self.save()

    def plus(self):
        self.x += 1
        self.save()

    def validate_x(self):
        return type(self.x) == int and self.x >= -1

    def red_if_negative(self):
        if self.x < 0:
            return 'red'
        return ''

    #def show_minus(self):
    #    return self.x != -1



