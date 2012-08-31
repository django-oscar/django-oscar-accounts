class BudgetException(Exception):
    pass


class InsufficientBudget(BudgetException):
    pass


class InvalidAmount(BudgetException):
    pass


class InactiveBudget(BudgetException):
    pass


class ClosedBudget(BudgetException):
    pass
