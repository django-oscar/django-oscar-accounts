from decimal import Decimal as D

from django.db.models import Sum
from oscar.core.loading import get_model

from oscar_accounts import names

AccountType = get_model('oscar_accounts', 'AccountType')
Account = get_model('oscar_accounts', 'Account')
Transfer = get_model('oscar_accounts', 'Transfer')


class ProfitLossReport(object):

    def __init__(self, start_datetime, end_datetime):
        self.start = start_datetime
        self.end = end_datetime

    def run(self):
        ctx = {}
        self.get_paid_loading_data(ctx)
        self.get_unpaid_loading_data(ctx)
        self.get_deferred_income_data(ctx)

        # Totals
        ctx['increase_total'] = (
            ctx['cash_total'] + ctx['unpaid_total'] + ctx['refund_total'])
        ctx['reduction_total'] = ctx['redeem_total'] + ctx['closure_total']
        ctx['position_difference'] = (
            ctx['increase_total'] - ctx['reduction_total'])

        return ctx

    def transfer_total(self, qs):
        filters = {
            'date_created__gte': self.start,
            'date_created__lt': self.end}
        transfers = qs.filter(**filters)
        total = transfers.aggregate(sum=Sum('amount'))['sum']
        return total if total is not None else D('0.00')

    def get_paid_loading_data(self, ctx):
        cash = AccountType.objects.get(name=names.CASH)
        cash_rows = []
        cash_total = D('0.00')
        for account in cash.accounts.all():
            total = self.transfer_total(account.source_transfers)
            cash_rows.append({
                'name': account.name,
                'total': total})
            cash_total += total
        ctx['cash_rows'] = cash_rows
        ctx['cash_total'] = cash_total

    def get_unpaid_loading_data(self, ctx):
        unpaid = AccountType.objects.get(name=names.UNPAID_ACCOUNT_TYPE)
        unpaid_rows = []
        unpaid_total = D('0.00')
        for account in unpaid.accounts.all():
            total = self.transfer_total(account.source_transfers)
            unpaid_rows.append({
                'name': account.name,
                'total': total})
            unpaid_total += total
        ctx['unpaid_rows'] = unpaid_rows
        ctx['unpaid_total'] = unpaid_total

    def get_deferred_income_data(self, ctx):
        deferred_income = AccountType.objects.get(
            name=names.DEFERRED_INCOME)
        redeem_rows = []
        closure_rows = []
        refund_rows = []
        redeem_total = closure_total = refund_total = D('0.00')
        redemptions_act = Account.objects.get(name=names.REDEMPTIONS)
        lapsed_act = Account.objects.get(name=names.LAPSED)
        for child in deferred_income.get_children():
            child_redeem_total = D('0.00')
            child_closure_total = D('0.00')
            child_refund_total = D('0.00')
            for account in child.accounts.all():
                # Look for transfers to the redemptions account
                qs = account.source_transfers.filter(
                    destination=redemptions_act)
                total = self.transfer_total(qs)
                child_redeem_total += total
                # Look for transfers to expired account
                qs = account.source_transfers.filter(
                    destination=lapsed_act)
                total = self.transfer_total(qs)
                child_closure_total += total
                # Look for transfers from redemptions account
                qs = redemptions_act.source_transfers.filter(
                    destination=account)
                child_refund_total += self.transfer_total(qs)
            redeem_rows.append({
                'name': child.name,
                'total': child_redeem_total})
            closure_rows.append({
                'name': child.name,
                'total': child_closure_total})
            refund_rows.append({
                'name': child.name,
                'total': child_refund_total})
            redeem_total += child_redeem_total
            closure_total += child_closure_total
            refund_total += child_refund_total

        ctx['redeem_rows'] = redeem_rows
        ctx['redeem_total'] = redeem_total
        ctx['closure_rows'] = closure_rows
        ctx['closure_total'] = closure_total
        ctx['refund_rows'] = refund_rows
        ctx['refund_total'] = refund_total
