from accounts.models import Account
from django.conf import settings
from django.db import models
from django.db.models.fields import DecimalField


class Transaction(models.Model):
    from_account = models.ForeignKey(
        Account,
        on_delete=models.DO_NOTHING,
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.DO_NOTHING,
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
    )
    amount = DecimalField()
