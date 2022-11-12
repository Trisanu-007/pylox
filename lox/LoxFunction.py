from LoxCallable import LoxCallable
import statements
from Environment import Environment
from LoxReturn import ReturnException


class LoxFunction(LoxCallable):
    def __init__(
        self,
        declaration: statements.Function,
        closure: Environment,
        is_initializer: bool,
    ) -> None:
        super().__init__()
        self.declaration = declaration
        self.closure = closure
        self.is_initializer = is_initializer

    def call(self, interpreter, arguments):
        environment = Environment(self.closure)
        for i in range(len(self.declaration.params)):
            environment.define(self.declaration.params[i].lexeme, arguments[i])
        try:
            interpreter.execute_block(self.declaration.body, environment)
        except ReturnException as rt:
            if self.is_initializer:
                return self.closure.get_at(0, "this")
            return rt.value

        if self.is_initializer:
            return self.closure.get_at(0, "this")
        return None

    def arity(self):
        return len(self.declaration.params)

    def __str__(self) -> str:
        return "<fn " + self.declaration.name.lexeme + ">"

    def bind(self, instance):
        environment = Environment(self.closure)
        environment.define("this", instance)
        return LoxFunction(self.declaration, environment, self.is_initializer)
