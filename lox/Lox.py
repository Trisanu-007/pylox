from TokenType import TokenType
from Scanner import Scanner
from Parser import Parser, ParseError
from ast_printer import ASTPrinter
from Interpreter import Interpreter
from pathlib import Path
from Resolver import Resolver


class Lox:
    had_error = False
    had_runtime_error = False
    interpreter = Interpreter()

    def report(self, line, where, message):
        print("[line " + line + "] Error" + where + ": " + message)
        Lox.had_error = True

    @staticmethod
    def error(self, token, message):
        if token.type == TokenType.EOF:
            self.report(token.line, " at end", message)
        else:
            self.report(token.line, " at '" + token.lexeme + "'", message)

    @staticmethod
    def runtime_error(err):
        print(f"{err} \n [ Line : {err.token.line} ]")

    @staticmethod
    def run(source):
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        parser = Parser(tokens)
        statements = parser.parse()

        if Lox.had_error:
            return

        # Lox.interpreter.interpret(statements=statements)
        interpreter = Interpreter()
        resolver = Resolver(interpreter=interpreter, on_error=Lox.error)
        resolver.resolve(statements=statements)

        if Lox.had_error:
            return

        interpreter.interpret(statements=statements)

    @staticmethod
    def run_file(filename):
        path = Path(filename).absolute()
        source = path.read_text(encoding="utf-8", errors="strict")
        Lox.run(source=source)

        if Lox.had_error:
            exit(65)
        elif Lox.had_runtime_error:
            exit(70)

    @staticmethod
    def run_prompt():
        while True:
            line = input(">> ")
            if line is None or line == "exit":
                break

            Lox.run(line)
            Lox.had_error = False
