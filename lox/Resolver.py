import expressions, statements
from Interpreter import Interpreter
from typing import List
from Token import Token
from TokenType import TokenType
from collections import deque
from enum import Enum, auto


class FunctionType(Enum):
    NONE = auto()
    FUNCTION = auto()
    METHOD = auto()
    INITIALIZER = auto()


class ClassType(Enum):
    NONE = auto()
    CLASS = auto()
    SUBCLASS = auto()


class Resolver(expressions.ExprVisitor, statements.StmtVisitor):
    def __init__(self, interpreter: Interpreter, on_error=None) -> None:
        super().__init__()
        self.interpreter = interpreter
        self.scopes = deque()
        self.on_error = on_error
        self.current_function = FunctionType.NONE
        self.current_class = ClassType.NONE

    def resolve(self, statements: List[statements.Stmt]):
        for statement in statements:
            self.resolve_one_statement(statement)

    def resolve_one_statement(self, stmt: statements.Stmt):
        stmt.accept(self)

    def resolve_expression(self, expr: statements.Expr):
        expr.accept(self)

    def begin_scope(self):
        self.scopes.append({})

    def end_scope(self):
        self.scopes.pop()

    def declare(self, name: Token):
        if len(self.scopes) == 0:
            return
        scope = self.scopes[-1]
        if name.lexeme in scope:
            self.on_error(name, "Already a variable with this name in this scope.")
        scope[name.lexeme] = False

    def define(self, name: Token):
        if len(self.scopes) == 0:
            return
        scope = self.scopes[-1]
        scope[name.lexeme] = True

    def resolve_local(self, expr: expressions.Expr, name: Token):
        for idx, scope in enumerate(reversed(self.scopes)):
            if name.lexeme in scope:
                self.interpreter.resolve(expr, idx)
                return

    def resolve_function(self, function: statements.Function, type: FunctionType):
        enclosing_function = self.current_function
        self.current_function = type

        self.begin_scope()
        for param in function.params:
            self.declare(param)
            self.define(param)

        self.resolve(function.body)
        self.end_scope()
        self.current_function = enclosing_function

    def visit_block_stmt(self, stmt: statements.Block):
        self.begin_scope()
        self.resolve(stmt.statements)
        self.end_scope()
        return None

    def visit_var_stmt(self, stmt: statements.Var):
        self.declare(stmt.name)
        if stmt.initializer is not None:
            self.resolve_expression(stmt.initializer)
        self.define(stmt.name)
        return None

    def visit_variable_expr(self, expr: expressions.Variable):
        if len(self.scopes) != 0 and self.scopes[-1].get(expr.name.lexeme) is False:
            self.on_error(
                expr.name, "Cannot read local variable in its own initializer."
            )

        self.resolve_local(expr, expr.name)
        return None

    def visit_assign_expr(self, expr: expressions.Assign):
        self.resolve_expression(expr.value)
        self.resolve_local(expr, expr.name)
        return None

    def visit_function_stmt(self, stmt: statements.Function):
        self.declare(stmt.name)
        self.define(stmt.name)

        self.resolve_function(stmt, FunctionType.FUNCTION)
        return None

    def visit_expression_stmt(self, stmt: statements.Expression):
        self.resolve_expression(stmt.expression)
        return None

    def visit_if_stmt(self, stmt: statements.If):
        self.resolve_expression(stmt.condition)
        self.resolve_one_statement(stmt.then_branch)

        if stmt.else_branch is not None:
            self.resolve_one_statement(stmt.else_branch)
        return None

    def visit_print_stmt(self, stmt: statements.Print):
        self.resolve_expression(stmt.expression)
        return None

    def visit_return_stmt(self, stmt: statements.Return):

        if self.current_function == FunctionType.NONE:
            self.on_error(stmt.keyword, "Can't return from top-level code.")

        if stmt.value is not None:

            if self.current_function == FunctionType.INITIALIZER:
                self.on_error(stmt.keyword, "Can't return a value from an initializer.")

            self.resolve_expression(stmt.value)
        return None

    def visit_while_stmt(self, stmt: statements.While):
        self.resolve_expression(stmt.condition)
        self.resolve_one_statement(stmt.body)
        return None

    def visit_binary_expr(self, expr: expressions.Binary):
        self.resolve_expression(expr.left)
        self.resolve_expression(expr.right)
        return None

    def visit_call_expr(self, expr: expressions.Call):
        self.resolve_expression(expr.callee)

        for arg in expr.arguments:
            self.resolve_expression(arg)

        return None

    def visit_grouping_expr(self, expr: expressions.Grouping):
        self.resolve_expression(expr.expression)
        return None

    def visit_literal_expr(self, expr: expressions.Literal):
        return None

    def visit_logical_expr(self, expr: expressions.Logical):
        self.resolve_expression(expr.left)
        self.resolve_expression(expr.right)
        return None

    def visit_unary_expr(self, expr: expressions.Unary):
        self.resolve_expression(expr.right)
        return None

    def visit_class_stmt(self, stmt: statements.Class):

        enclosing_class = self.current_function
        self.current_class = ClassType.CLASS

        self.declare(stmt.name)
        self.define(stmt.name)

        if (
            stmt.superclass is not None
            and stmt.name.lexeme == stmt.superclass.name.lexeme
        ):
            self.on_error(stmt.superclass.name, "A class can't inherit from itself.")

        if stmt.superclass is not None:
            self.current_class = ClassType.SUBCLASS
            self.resolve_expression(stmt.superclass)

        if stmt.superclass is not None:
            self.begin_scope()
            self.scopes[-1]["super"] = True

        self.begin_scope()
        self.scopes[-1]["this"] = True

        for method in stmt.methods:
            declaration = FunctionType.METHOD
            if method.name.lexeme == "init":
                declaration = FunctionType.INITIALIZER
            self.resolve_function(method, declaration)

        self.end_scope()
        if stmt.superclass is not None:
            self.end_scope()
        self.current_class = enclosing_class
        return None

    def visit_get_expr(self, expr: expressions.Get):
        self.resolve_expression(expr.obj)
        return None

    def visit_set_expr(self, expr: expressions.Set):
        self.resolve_expression(expr.value)
        self.resolve_expression(expr.obj)

    def visit_super_expr(self, expr: expressions.Super):
        if self.current_class == ClassType.NONE:
            self.on_error(expr.keyword, "Can't use 'super' outside of a class.")
        elif self.current_class != ClassType.SUBCLASS:
            self.on_error(
                expr.keyword, "Can't use 'super' in a class with no superclass."
            )

        self.resolve_local(expr=expr, name=expr.keyword)
        return None

    def visit_this_expr(self, expr: expressions.This):
        if self.current_class == ClassType.NONE:
            self.on_error(expr.keyword, "Can't use 'this' outside of a class.")
            return None

        self.resolve_local(expr, expr.keyword)
        return None
