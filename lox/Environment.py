from typing import Dict, Optional
from Token import Token


class EnvironmentError(RuntimeError):
    def __init__(self, token, message):
        super().__init__(message)
        self.token = token


class Environment:
    def __init__(self, enclosing=None):
        self.values = dict()
        self.enclosing = enclosing

    def define(self, name, value):
        self.values[name] = value

    def get(self, name: Token):
        if name.lexeme in self.values.keys():
            return self.values[name.lexeme]

        if self.enclosing is not None:
            return self.enclosing.get(name)

        raise EnvironmentError(name, "Undefined variable '" + name.lexeme + "'.")

    def assign(self, name: Token, value):
        if name.lexeme in self.values.keys():
            self.values[name.lexeme] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return

        raise EnvironmentError(name, "Undefined variable '" + name.lexeme + "'.")
