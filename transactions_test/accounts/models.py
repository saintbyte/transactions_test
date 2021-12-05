from django.conf import settings
from django.db import models


class Account(models.Model):
    holder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=128)
    is_active = models.BooleanField(default=False)
    balance = models.DecimalField()

    def str(self):
        return self.name

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
