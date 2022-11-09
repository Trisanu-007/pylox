from Token import Token
from TokenType import TokenType


class Scanner:
    def __init__(self, source):
        self.source = source
        self.tokens = list()
        self.start = 0
        self.current = 0
        self.line = 1

        self.keywords = dict()
        self.keywords["and"] = TokenType.AND
        self.keywords["class"] = TokenType.CLASS
        self.keywords["false"] = TokenType.FALSE
        self.keywords["for"] = TokenType.FOR
        self.keywords["fun"] = TokenType.FUN
        self.keywords["if"] = TokenType.IF
        self.keywords["nil"] = TokenType.NIL
        self.keywords["or"] = TokenType.OR
        self.keywords["print"] = TokenType.PRINT
        self.keywords["return"] = TokenType.RETURN
        self.keywords["super"] = TokenType.SUPER
        self.keywords["this"] = TokenType.THIS
        self.keywords["true"] = TokenType.TRUE
        self.keywords["var"] = TokenType.VAR
        self.keywords["while"] = TokenType.WHILE

        self.not_in_lst = [" ", "\r", "\t"]

    def scan_tokens(self):
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def is_at_end(self):
        return self.current >= len(self.source)

    def advance(self):
        text = self.source[self.current]
        self.current += 1
        return text

    def add_one_token(self, type, literal):
        text = self.source[self.start : self.current]
        self.tokens.append(
            Token(type=type, lexeme=text, literal=literal, line=self.line)
        )

    def add_token(self, type):
        self.add_one_token(type, None)

    def match(self, expected):
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def peek(self):
        if self.is_at_end():
            return "\0"
        return self.source[self.current]

    def string(self):
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == "\n":
                self.line += 1
            self.advance()

        if self.is_at_end():
            # TODO : Change this
            print(self.line, "Unterminated string.")

        self.advance()
        value = self.source[self.start + 1 : self.current - 1]
        self.add_one_token(type=TokenType.STRING, literal=value)

    def is_digit(self, c: str):
        return c.isdigit()

    def number(self):
        while self.is_digit(self.peek()):
            self.advance()
        if self.peek() == "." and self.is_digit(self.peek_next()):
            self.advance()
            while self.is_digit(self.peek()):
                self.advance()

        self.add_one_token(
            type=TokenType.NUMBER, literal=float(self.source[self.start : self.current])
        )

    def peek_next(self):
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def is_alpha(self, c):
        return (c >= "a" and c <= "z") or (c >= "A" and c <= "Z") or c == "_"

    def is_alpha_numeric(self, c: str):
        return self.is_alpha(c) or c.isdigit()

    def identifier(self):
        while self.is_alpha_numeric(self.peek()):
            self.advance()

        text = self.source[self.start : self.current]
        type = self.keywords[text] if text in self.keywords.keys() else None
        if type is None:
            type = TokenType.IDENTIFIER
        self.add_token(type=type)

    def scan_token(self):
        c = self.advance()
        if c == "(":
            self.add_token(TokenType.LEFT_PAREN)
        elif c == ")":
            self.add_token(TokenType.RIGHT_PAREN)
        elif c == "{":
            self.add_token(TokenType.LEFT_BRACE)
        elif c == "}":
            self.add_token(TokenType.RIGHT_BRACE)
        elif c == ",":
            self.add_token(TokenType.COMMA)
        elif c == ".":
            self.add_token(TokenType.DOT)
        elif c == "-":
            self.add_token(TokenType.MINUS)
        elif c == "+":
            self.add_token(TokenType.PLUS)
        elif c == ";":
            self.add_token(TokenType.SEMICOLON)
        elif c == "*":
            self.add_token(TokenType.STAR)
        elif c == "!":
            self.add_token(
                TokenType.BANG_EQUAL if self.match("=") else TokenType.BANG_EQUAL
            )
        elif c == "=":
            self.add_token(
                TokenType.EQUAL_EQUAL if self.match("=") else TokenType.EQUAL
            )
        elif c == "<":
            self.add_token(TokenType.LESS_EQUAL if self.match("=") else TokenType.LESS)
        elif c == ">":
            self.add_token(
                TokenType.GREATER_EQUAL if self.match("=") else TokenType.GREATER
            )
        elif c == "/":
            if self.match("/"):
                while self.peek() != "\n" and not self.is_at_end():
                    self.advance()
            else:
                self.add_token(TokenType.SLASH)
        elif c == "\n":
            self.line += 1
        elif c == '"':
            self.string()

        else:
            # TODO : Change this
            if c.isdigit():
                self.number()
            elif self.is_alpha(c):
                self.identifier()
            elif c not in self.not_in_lst:
                print(self.line, "Unexpected character.")
