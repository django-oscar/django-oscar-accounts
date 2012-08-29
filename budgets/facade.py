from budgets import models


def transfer(source, destination, amount):
    models.Transaction.objects.create(
        budget=source,
        amount=-amount)
    models.Transaction.objects.create(
        budget=destination,
        amount=amount)
