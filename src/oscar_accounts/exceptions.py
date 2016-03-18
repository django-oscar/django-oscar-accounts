class AccountException(Exception):
    pass


class AccountNotEmpty(AccountException):
    pass


class InsufficientFunds(AccountException):
    pass


class InvalidAmount(AccountException):
    pass


class InactiveAccount(AccountException):
    pass


class ClosedAccount(AccountException):
    pass
