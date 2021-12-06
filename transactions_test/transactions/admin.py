from django.contrib import admin
from transactions.models import Transaction


class TransactionAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        "creator",
    ]
    readonly_fields = ["request_id", "amount"]
    list_display = [
        "from_account",
        "to_account",
        "creator",
        "request_id",
        "type_of_transaction",
        "processed",
        "amount",
    ]


admin.site.register(Transaction, TransactionAdmin)
