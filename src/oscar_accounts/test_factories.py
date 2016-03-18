from decimal import Decimal as D

import factory
from oscar.core.loading import get_model


class AccountFactory(factory.DjangoModelFactory):
    start_date = None
    end_date = None

    class Meta:
        model = get_model('oscar_accounts', 'Account')


class TransferFactory(factory.DjangoModelFactory):
    source = factory.SubFactory(AccountFactory)
    destination = factory.SubFactory(AccountFactory)

    class Meta:
        model = get_model('oscar_accounts', 'Transfer')

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        instance = model_class(**kwargs)
        instance.save()
        return instance


class TransactionFactory(factory.DjangoModelFactory):
    amount = D('10.00')
    transfer = factory.SubFactory(
        TransferFactory, amount=factory.SelfAttribute('..amount'))
    account = factory.SubFactory(AccountFactory)

    class Meta:
        model = get_model('oscar_accounts', 'Transaction')
