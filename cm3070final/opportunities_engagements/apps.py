from django.apps import AppConfig


class OpportunitiesEngagementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opportunities_engagements'

    def ready(self):
        import opportunities_engagements.signals