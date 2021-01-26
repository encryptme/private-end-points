import json

import six

from cloak.serverapi.server import Server
from cloak.serverapi.utils.encoding import force_text

from ._base import BaseCommand


class Command(BaseCommand):
    brief = "Show information about this server"
    description = "Shows information about this server."

    def add_arguments(self, parser, group):
        group.add_argument('-j', '--json', action='store_true', help="Output the API results directly as JSON.")

    def handle(self, config, **options):
        server_id, auth_token = self._require_credentials(config)

        server = Server.retrieve(server_id, auth_token)

        if options['json']:
            json.dump(server, self.stdout)
        else:
            self._print_server(server)
