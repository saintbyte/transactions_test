from accounts.models import Account
from django.conf import settings
from django.db import models
from transactions.constants import DECIMAL_MAX_DIGITS
from transactions.constants import DECIMAL_PLACES
from transactions.constants import SIMPLE_TRANSACTION
from transactions.constants import TYPE_OF_TRANSACTION_CHOICES


class Transaction(models.Model):
    from_account = models.ForeignKey(
        Account,
        related_name="from_account",
        on_delete=models.DO_NOTHING,
    )
    to_account = models.ForeignKey(
        Account,
        related_name="to_account",
        on_delete=models.DO_NOTHING,
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="creator",
        on_delete=models.DO_NOTHING,
    )
    request_id = models.CharField(
        null=True,
        max_length=128,
        unique=True,
        verbose_name="Client side random unique random value",
    )
    type_of_transaction = models.CharField(
        max_length=64,
        choices=TYPE_OF_TRANSACTION_CHOICES,
        default=SIMPLE_TRANSACTION,
    )
    processed = models.BooleanField(
        default=False, verbose_name="Transaction WAS processed"
    )
    amount = models.DecimalField(
        max_digits=DECIMAL_MAX_DIGITS, decimal_places=DECIMAL_PLACES
    )

    def accept(self):
        self.processed = True
        self.save()
