from django.contrib import admin

from accounts import models


class AccountAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'primary_user', 'credit_limit',
                    'start_date', 'end_date', 'is_active', 'balance',
                    'date_created']


class TransferAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'description', 'date_created']
    readonly_fields = ('description', 'user', 'username', 'date_created')


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'transaction', 'account', 'amount', 'date_created']
    readonly_fields = ('transaction', 'account', 'amount', 'date_created')


admin.site.register(models.Account, AccountAdmin)
admin.site.register(models.Transfer, TransferAdmin)
admin.site.register(models.Transaction, TransactionAdmin)
