from __future__ import absolute_import, division, print_function, unicode_literals

from cloak.serverapi.server import Server

from ._base import BaseCommand


class Command(BaseCommand):
    brief = "Show information about this server"
    description = "Shows information about this server."

    def handle(self, config, **options):
        server_id, auth_token = self._require_credentials(config)

        server = Server.retrieve(server_id, auth_token)

        self._print_server(server)
