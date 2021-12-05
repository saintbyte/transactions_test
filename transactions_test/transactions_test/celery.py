from __future__ import absolute_import
from __future__ import unicode_literals

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transactions_test.settings")
app = Celery("transactions_test")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
