from typing import List
import expressions
from TokenType import TokenType
from Token import Token
import statements
from Environment import Environment
from LoxCallable import LoxCallable
from LoxClock import Clock
from LoxFunction import LoxFunction
from LoxReturn import ReturnException


class LoxRuntimeError(RuntimeError):
    def __init__(self, token, message) -> None:
        super().__init__(message)
        self.token = token

    def __str__(self) -> str:
        return super().__str__()

    def __repr__(self) -> str:
        return super().__repr__()


class Interpreter(expressions.ExprVisitor, statements.StmtVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.globals = Environment()
        self.environment = self.globals
        self.globals.define("clock", Clock())

    def evaluate(self, expr: expressions.Expr):
        return expr.accept(self)

    def execute(self, stmt: statements.Stmt):
        stmt.accept(self)

    def is_truthy(self, obj):
        if obj is None:
            return False
        if type(obj) == bool:
            return bool(obj)
        return True

    def execute_block(
        self, statements: List[statements.Stmt], environment: Environment
    ):
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def visit_if_stmt(self, stmt: statements.If):
        if self.is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            self.execute(stmt.else_branch)

    def visit_block_stmt(self, stmt: statements.Block):
        self.execute_block(stmt.statements, Environment(self.environment))

    def visit_expression_stmt(self, expr: statements.Expression):
        self.evaluate(expr.expression)

    def visit_print_stmt(self, stmt: statements.Print):
        value = self.evaluate(stmt.expression)
        print(self.stringify(value))
        return None

    def visit_var_stmt(self, stmt: statements.Var):
        value = None
        if stmt.initializer is not None:
            value = self.evaluate(stmt.initializer)
        self.environment.define(name=stmt.name.lexeme, value=value)
        return None

    def visit_variable_expr(self, expr: expressions.Variable):
        return self.environment.get(expr.name)

    def check_number_operand_unary(self, operator, operand):
        if type(operand) == float:
            return
        raise LoxRuntimeError(operator, "Operand must be a number.")

    def check_number_operands(self, operator, left, right):
        if type(left) == float and type(right) == float:
            return
        raise LoxRuntimeError(operator, "Operands must be numbers.")

    def visit_literal_expr(self, expr):
        return expr.value

    def visit_grouping_expr(self, expr):
        return self.evaluate(expr.expression)

    def visit_unary_expr(self, expr: expressions.Unary):
        right = self.evaluate(expr.right)

        if expr.operator.type == TokenType.MINUS:
            self.check_number_operand_unary(expr.operator, right)
            return -(float(right))
        if expr.operator.type == TokenType.BANG:
            return not self.is_truthy(right)

        return None

    def is_equal(self, a, b):
        if a is None and b is None:
            return True
        if a is None:
            return False
        return a == b

    def visit_binary_expr(self, expr: expressions.Binary):
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)

        if expr.operator.type == TokenType.MINUS:
            self.check_number_operands(expr.operator, left, right)
            return (float(left)) - (float(right))

        if expr.operator.type == TokenType.SLASH:
            return (float(left)) / (float(right))

        if expr.operator.type == TokenType.STAR:
            self.check_number_operands(expr.operator, left, right)
            return (float(left)) * (float(right))

        if expr.operator.type == TokenType.PLUS:

            if type(left) == float and type(right) == float:
                return float(left) + float(right)

            if type(left) == str and type(right) == str:
                return str(left) + str(right)

            raise LoxRuntimeError(
                expr.operator, "Operands must be two numbers or two strings."
            )

        if expr.operator.type == TokenType.GREATER:
            self.check_number_operands(expr.operator, left, right)
            return (float(left)) > (float(right))

        if expr.operator.type == TokenType.GREATER_EQUAL:
            self.check_number_operands(expr.operator, left, right)
            return (float(left)) >= (float(right))

        if expr.operator.type == TokenType.LESS:
            self.check_number_operands(expr.operator, left, right)
            return (float(left)) < (float(right))

        if expr.operator.type == TokenType.LESS_EQUAL:
            self.check_number_operands(expr.operator, left, right)
            return (float(left)) <= (float(right))

        if expr.operator.type == TokenType.BANG_EQUAL:
            return not self.is_equal(left, right)

        if expr.operator.type == TokenType.EQUAL_EQUAL:
            return self.is_equal(left, right)

        return None

    def visit_function_stmt(self, stmt: statements.Stmt):
        function = LoxFunction(stmt)
        self.environment.define(stmt.name.lexeme, function)

    def interpret(self, statements: List[statements.Stmt]):
        try:
            for stmt in statements:
                self.execute(stmt)
        except LoxRuntimeError as loxe:
            print(loxe)

    def stringify(self, object):
        if object is None:
            return "nil"
        if isinstance(object, float):
            text = str(object)
            if text[-2:] == ".0":
                text = text[:-2]
            return text
        return str(object)

    def visit_assign_expr(self, expr: expressions.Assign):
        value = self.evaluate(expr.value)
        self.environment.assign(expr.name, value)
        return value

    def visit_while_stmt(self, stmt: statements.While):
        while self.is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.body)

    def visit_call_expr(self, expr: expressions.Call):
        callee = self.evaluate(expr.callee)
        arguments = []
        for argument in expr.arguments:
            arguments.append(self.evaluate(argument))

        if not isinstance(callee, LoxCallable):
            raise LoxRuntimeError(expr.paren, "Can only call functions and classes.")

        function: LoxCallable = callee
        if len(arguments) != function.arity():
            raise LoxRuntimeError(
                expr.paren,
                "Expected "
                + function.arity()
                + " arguments but got "
                + arguments.size()
                + ".",
            )

        return function.call(self, arguments)

    def visit_return_stmt(self, stmt: statements.Return):
        value = None
        if stmt.value is not None:
            value = self.evaluate(stmt.value)

        raise ReturnException(value)

    def visit_get_expr(self, expr):
        return super().visit_get_expr(expr)

    def visit_logical_expr(self, expr: expressions.Logical):
        left = self.evaluate(expr.left)

        if expr.operator.type == TokenType.OR:
            if self.is_truthy(left):
                return left
            else:
                if not self.is_truthy(left):
                    return left

            return self.evaluate(expr.right)

    def visit_set_expr(self, expr):
        return super().visit_set_expr(expr)

    def visit_super_expr(self, expr):
        return super().visit_super_expr(expr)

    def visit_this_expr(self, expr):
        return super().visit_this_expr(expr)
