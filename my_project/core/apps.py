from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """
        Importar las señales cuando la app esté lista.
        Esto asegura que los perfiles se creen automáticamente.
        """
        import core.signals