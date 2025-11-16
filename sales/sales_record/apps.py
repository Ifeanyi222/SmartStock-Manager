from django.apps import AppConfig


class SalesRecordConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sales_record"

    def ready(self):
        import sales_record.signals
