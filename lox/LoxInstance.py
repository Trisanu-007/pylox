from LoxRuntimeError import LoxRuntimeError


class LoxInstance:
    def __init__(self, klass) -> None:
        self.klass = klass
        self.fields = dict()

    def __str__(self) -> str:
        return self.klass + " instance"

    def get(self, name):
        if name.lexeme in self.fields.keys():
            return self.fields[name.lexeme]

        method = self.klass.find_method(name.lexeme)
        if method is not None:
            return method.bind(self)

        raise LoxRuntimeError(name, "Undefined property '" + name.lexeme + "'.")

    def set(self, name, value):
        self.fields[name.lexeme] = value