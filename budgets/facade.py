from budgets.models import TransactionID


def transfer(source, destination, amount, user):
    """
    Transfer funds between source budget and destination budget

    :source: Budget to debit
    :destination: Budget to credit
    :amount: Amount to transfer
    :user: Authorising user
    """
    txn_id = TransactionID.new()
    source._debit(txn_id, amount, user)
    destination._credit(txn_id, amount, user)
    return txn_id
