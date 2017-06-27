from __future__ import unicode_literals

from django.apps import AppConfig


class EscapadConfig(AppConfig):
    name = 'escapad'

    def ready(self):
        # import signal handlers, which allow to register them
        # right away (otherwise they would never been registered
        # nor called)
        import escapad.signals
