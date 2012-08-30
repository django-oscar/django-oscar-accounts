from django.contrib import admin

from budgets import models


class BudgetAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'primary_user', 'credit_limit',
                    'start_date', 'end_date', 'is_active', 'balance',
                    'date_created']


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'description', 'date_created']
    readonly_fields = ('description', 'user', 'username', 'date_created')


class BudgetTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'transaction', 'budget', 'amount', 'date_created']
    readonly_fields = ('transaction', 'budget', 'amount', 'date_created')


admin.site.register(models.Budget, BudgetAdmin)
admin.site.register(models.Transaction, TransactionAdmin)
admin.site.register(models.BudgetTransaction, BudgetTransactionAdmin)
