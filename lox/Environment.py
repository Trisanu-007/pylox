from typing import Dict
from Token import Token


class EnvironmentError(RuntimeError):
    def __init__(self, token, message):
        super().__init__(message)
        self.token = token


class Environment:
    def __init__(self):
        self.values = dict()

    def define(self, name, value):
        self.values[name] = value

    def get(self, name: Token):
        if name.lexeme in self.values.keys():
            return self.values[name.lexeme]

        raise EnvironmentError(name, "Undefined variable '" + name.lexeme + "'.")
