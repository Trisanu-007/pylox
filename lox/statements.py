from abc import ABC, abstractmethod
from Token import Token
from expressions import Expr


class StmtVisitor(ABC):
    @abstractmethod
    def visit_expression_stmt(self, expr: "Stmt"):
        pass

    @abstractmethod
    def visit_print_stmt(self, expr: "Stmt"):
        pass

    @abstractmethod
    def visit_var_stmt(self, expr: "Stmt"):
        pass


class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: StmtVisitor):
        pass
  # Chnge to return self

class Expression(Stmt):
    def __init__(self, expression: Expr) -> None:
        self.expression = expression

    def accept(self, visitor: StmtVisitor) -> None:
        return visitor.visit_expression_stmt(self)


class Print(Stmt):
    def __init__(self, expression: Expr) -> None:
        self.expression = expression

    def accept(self, visitor: StmtVisitor) -> None:
        return visitor.visit_print_stmt(self)


class Var(Stmt):
    def __init__(self, name: Token, initializer: Expr) -> None:
        self.name = name
        self.initializer = initializer

    def accept(self, visitor: StmtVisitor) -> None:
        return visitor.visit_var_stmt(self)
