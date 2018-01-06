from __future__ import absolute_import, division, print_function, unicode_literals

import os.path

from oscrypto import asymmetric
import six

from cloak.serverapi.server import Server

from ._base import BaseCommand, CommandError


class Command(BaseCommand):
    brief = "Request a server certificate"
    description = "Request a server certificate. You should only need to do this once."

    def add_arguments(self, parser, group):
        group.add_argument('-k', '--key', required=True, help="Path to the private key. They key will be created if it doesn't exist.")

    def handle(self, config, key, **options):
        server_id, auth_token = self._require_credentials(config)

        key_pem = self._load_key(six.text_type(key))

        server = Server.retrieve(server_id, auth_token)
        success = server.request_certificate(key_pem)

        if success:
            print("A new certificate has been requested. If you have not enabled automatic PKI approval this request must be approved on your team dashboard.", file=self.stdout)
        else:
            raise CommandError("An unknown error occurred while trying to request a certificate.")

    #
    # Key management
    #

    def _load_key(self, path):
        # type: (str) -> str
        if os.path.exists(path):
            key_pem = self._read_key(path)
        else:
            key_pem = self._generate_key(path)

        return key_pem

    def _read_key(self, path):
        # type: (str) -> str
        try:
            privkey = asymmetric.load_private_key(path)
        except Exception as e:
            raise CommandError("Error reading private key at {}: {}".format(path, e))

        key_pem = asymmetric.dump_private_key(privkey, None, 'pem')

        return key_pem

    def _generate_key(self, path):
        # type: (str) -> str
        try:
            with open(path, 'wb') as f:
                _, privkey = asymmetric.generate_pair('rsa', bit_size=2048)
                key_pem = asymmetric.dump_private_key(privkey, None, 'pem')
                f.write(key_pem)
        except IOError:
            raise CommandError("{} is not a path to a writable file.".format(path))

        return key_pem
