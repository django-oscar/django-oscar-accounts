class BudgetException(Exception):
    pass


class InsufficientBudget(BudgetException):
    pass


class InvalidAmount(BudgetException):
    pass
