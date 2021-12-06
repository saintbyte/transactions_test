from accounts.models import Account
from django.conf import settings
from django.contrib import admin


class AccountAdmin(admin.ModelAdmin):
    if not settings.DEBUG:
        readonly_fields = ["balance"]


admin.site.register(Account, AccountAdmin)
