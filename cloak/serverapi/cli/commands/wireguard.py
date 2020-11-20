from __future__ import absolute_import, division, print_function, unicode_literals

import json

import six

from cloak.serverapi.server import Server
from cloak.serverapi.utils.encoding import force_text

from ._base import BaseCommand


class Command(BaseCommand):
    brief = "Retreives information about WireGuard peers"
    description = "Retreives information about WireGuard peers."

    def add_arguments(self, parser, group):
        pass

    def handle(self, config, **options):
        server_id, auth_token = self._require_credentials(config)

        peers = Server.wireguard_peers(server_id, auth_token)

        if six.PY3:
            json.dump(server, self.stdout)
        else:
            print(force_text(json.dumps(peers)), file=self.stdout)
