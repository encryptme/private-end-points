import json

import six

from cloak.serverapi.server import Server
from cloak.serverapi.utils.encoding import force_text

from ._base import BaseCommand


class Command(BaseCommand):
    brief = "Show information about this server"
    description = "Shows information about this server."

    def add_arguments(self, parser, group):
        group.add_argument('-n', '--name', help="Update the server name.")
        group.add_argument('-a', '--api-version', help="Update the server's default API version.")
        group.add_argument('-j', '--json', action='store_true', help="Output the API results directly as JSON.")

    def handle(self, config, name, api_version, **options):
        server_id, auth_token = self._require_credentials(config)

        server = Server.retrieve(server_id, auth_token)
        server.update_server(name=name, api_version=api_version)

        if options['json']:
            json.dump(server, self.stdout)
        else:
            self._print_server(server)
