from TokenType import TokenType
from Token import Token
from typing import List, Optional
import expressions
import statements


class ParseError(RuntimeError):
    def __init__(self, token, message) -> None:
        super().__init__(message)
        self.token = token


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def expression(self) -> expressions.Expr:
        return self.assignment()

    def equality(self) -> expressions.Expr:
        expr = self.comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self.previous()
            right = self.comparison()
            expr = expressions.Binary(expr, operator, right)

        return expr

    def comparison(self):
        expr = self.term()
        while self.match(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            operator = self.previous()
            right = self.term()
            expr = expressions.Binary(expr, operator, right)

        return expr

    def match(self, *types):
        for type in types:
            if self.check(type):
                self.advance()
                return True

        return False

    def check(self, cls_type):
        if self.is_at_end():
            return False
        return self.peek().type == cls_type

    def advance(self):
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self):
        return self.peek().type == TokenType.EOF

    def peek(self):
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def term(self):
        expr = self.factor()
        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous()
            right = self.factor()
            expr = expressions.Binary(expr, operator, right)

        return expr

    def factor(self):
        expr = self.unary()
        while self.match(TokenType.SLASH, TokenType.STAR):
            operator = self.previous()
            right = self.unary()
            expr = expressions.Binary(expr, operator, right)

        return expr

    def finish_call(self, callee):
        arguments = []
        if not self.check(TokenType.RIGHT_PAREN):
            arguments.append(self.expression())
            while self.match(TokenType.COMMA):
                if len(arguments) >= 255:
                    self.error(self.peek(), "Cannot have more than 255 arguments.")
                arguments.append(self.expression())

        paren = self.consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")
        return expressions.Call(callee, paren, arguments)

    def call(self):
        expr = self.primary()

        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.DOT):
                name = self.consume(
                    TokenType.IDENTIFIER, "Expect property name after '.'."
                )
                expr = expressions.Get(expr, name)
            else:
                break

        return expr

    def unary(self):
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return expressions.Unary(operator=operator, right=right)

        return self.call()

    def function(self, kind: str):
        name = self.consume(TokenType.IDENTIFIER, "Expect " + kind + " name.")
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after " + kind + " name.")
        parameters = []

        if not self.check(TokenType.RIGHT_PAREN):
            # if len(parameters) >= 255:
            #     self.error(self.peek(), "Can't have more than 255 parameters.")
            parameters.append(
                self.consume(TokenType.IDENTIFIER, "Expect parameter name.")
            )

            while self.match(TokenType.COMMA):
                if len(parameters) >= 255:
                    self.error(self.peek(), "Can't have more than 255 parameters.")
                parameters.append(
                    self.consume(TokenType.IDENTIFIER, "Expect parameter name.")
                )

        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")
        self.consume(TokenType.LEFT_BRACE, "Expect '{' before " + kind + " body.")
        body = self.block()
        return statements.Function(name, parameters, body)

    def primary(self):

        if self.match(TokenType.FUN):
            return self.function("function")
        if self.match(TokenType.FALSE):
            return expressions.Literal(False)
        if self.match(TokenType.TRUE):
            return expressions.Literal(True)
        if self.match(TokenType.NIL):
            return expressions.Literal(None)
        if self.match(TokenType.THIS):
            return expressions.This(self.previous())
        if self.match(TokenType.NUMBER, TokenType.STRING):
            return expressions.Literal(self.previous().literal)

        if self.match(TokenType.SUPER) : 
            keyword = self.previous()
            self.consume(TokenType.DOT, "Expect '.' after 'super'.")
            method = self.consume(TokenType.IDENTIFIER, "Expect superclass method name.")
            return expressions.Super(keyword=keyword, method=method)

        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return expressions.Grouping(expr)

        if self.match(TokenType.IDENTIFIER):
            return expressions.Variable(self.previous())

        raise self.error(self.peek(), "Expect expression.")

    def consume(self, type, message):
        if self.check(type):
            return self.advance()

        raise self.error(self.peek(), message)

    def error(self, token, message):
        return ParseError(token, message)

    def synchronize(self):

        self.advance()
        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return

            if self.peek().type in (
                TokenType.CLASS,
                TokenType.FUN,
                TokenType.VAR,
                TokenType.FOR,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.PRINT,
                TokenType.RETURN,
            ):
                return

            self.advance()

    def print_statement(self):
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return statements.Print(value)

    def expression_statement(self):
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return statements.Expression(expr)

    def block(self):
        statements = []

        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def and_statement(self):
        expr = self.equality()

        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.equality()
            expr = expressions.Logical(expr, operator, right)

        return expr

    def or_statement(self):
        expr = self.and_statement()

        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.and_statement()
            expr = expressions.Logical(expr, operator, right)

        return expr

    def assignment(self):
        expr: expressions.Variable = self.or_statement()

        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()

            if isinstance(expr, expressions.Variable):
                name = expr.name
                return expressions.Assign(name, value)
            elif isinstance(expr, expressions.Get):
                get: expressions.Get = expr
                return expressions.Set(get.obj, get.name, value)

            self.error(equals, "Invalid assignment target.")

        return expr

    def if_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after 'if' condition.")

        then_branch = self.statement()
        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.statement()

        return statements.If(condition, then_branch, else_branch)

    def while_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_BRACE, "Expect ')' after 'condition'.")
        body = self.statement()

        return statements.While(condition, body)

    def for_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        initializer = None
        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.match(TokenType.VAR):
            initializer = self.var_declaration()
        else:
            initializer = self.expression_statement()

        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        increment = None
        if not self.check(TokenType.RIGHT_PAREN):
            increment = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        body = self.statement()

        if increment is not None:
            body = statements.Block([body, statements.Expression(increment)])

        if condition == None:
            condition = expressions.Literal(True)
        body = statements.While(condition, body)

        if initializer is not None:
            body = statements.Block([initializer, body])

        return body

    def return_statement(self):
        keyword = self.previous()
        value = None

        if not self.check(TokenType.SEMICOLON):
            value = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return statements.Return(keyword, value)

    def statement(self):
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.FOR):
            return self.for_statement()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.PRINT):
            return self.print_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.LEFT_BRACE):
            return statements.Block(self.block())

        return self.expression_statement()

    def class_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, "Expect class name.")

        superclass = None
        if self.match(TokenType.LESS):
            self.consume(TokenType.IDENTIFIER, "Expect superclass name.")
            superclass = expressions.Variable(self.previous())

        self.consume(TokenType.LEFT_BRACE, "Expect '{' before class body.")

        methods = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            methods.append(self.function("method"))

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")
        return statements.Class(name, methods, superclass=superclass)

    def declaration(self):
        try:
            if self.match(TokenType.CLASS):
                return self.class_declaration()
            if self.match(TokenType.FUN):
                return self.function("function")
            if self.match(TokenType.VAR):
                return self.var_declaration()
            return self.statement()
        except ParseError as err:
            self.synchronize()
            return None

    def var_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, "Expect variable name.")
        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return statements.Var(name=name, initializer=initializer)

    def parse(self):
        statements = list()
        while not self.is_at_end():
            statements.append(self.declaration())

        return statements
