from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    verbose_name = "AutoPonto API"

    def ready(self):
        import api.schema  # noqa: F401
