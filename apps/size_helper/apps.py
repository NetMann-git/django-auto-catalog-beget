# apps/size_helper/apps.py

from django.apps import AppConfig


class SizeHelperConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.size_helper"   # ← должно быть так