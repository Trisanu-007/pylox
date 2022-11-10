from LoxCallable import LoxCallable
import statements
from Environment import Environment
from LoxReturn import ReturnException


class LoxFunction(LoxCallable):
    def __init__(self, declaration: statements.Function) -> None:
        super().__init__()
        self.declaration = declaration

    def call(self, interpreter, arguments):
        environment = Environment(interpreter.globals)
        for i in range(len(self.declaration.params)):
            environment.define(self.declaration.params[i].lexeme, arguments[i])
        try:
            interpreter.execute_block(self.declaration.body, environment)
        except ReturnException as rt:
            return rt.value
        return None

    def arity(self):
        return len(self.declaration.params)

    def __str__(self) -> str:
        return "<fn " + self.declaration.name.lexeme + ">"
