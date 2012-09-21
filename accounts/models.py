from accounts import abstract_models


class AccountType(abstract_models.AccountType):
    pass


class Account(abstract_models.Account):
    pass


class Transfer(abstract_models.Transfer):
    pass


class Transaction(abstract_models.Transaction):
    pass


class IPAddressRecord(abstract_models.IPAddressRecord):
    pass
