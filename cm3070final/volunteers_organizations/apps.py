from django.apps import AppConfig


class VolunteersOrganizationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'volunteers_organizations'

    def ready(self):
        import volunteers_organizations.signals