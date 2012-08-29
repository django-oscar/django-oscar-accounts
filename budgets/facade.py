from budgets import models


def transfer(source, destination, amount):
    source._debit(amount)
    destination._credit(amount)
