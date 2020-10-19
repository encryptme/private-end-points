import os
import os.path
import subprocess
import time

from six.moves.configparser import ConfigParser, NoOptionError  # noqa
from typing import cast

from cloak.serverapi.server import Server, PKI

from ._base import BaseCommand, CommandError


class Command(BaseCommand):
    brief = "Download current certificates"
    description = "Downloads current certificates and other PKI information."

    def add_arguments(self, parser, group):
        group.add_argument('-o', '--out', default=os.getcwd(), help="Where to download the certificates. Defaults to the current directory.")
        group.add_argument('-f', '--force', action='store_true', help="Ignore any existing tag and always download the certificates.")
        group.add_argument('-w', '--wait', action='store_true', help="If a certificate request is pending, wait for it to be approved.")
        group.add_argument('-p', '--post-hook', help="Command to run if the certificates were updated. This will be run in a shell.")

    def handle(self, config, out, force, wait, post_hook, **options):
        server_id, auth_token = self._require_credentials(config)

        server = Server.retrieve(server_id, auth_token)

        while wait and server.csr_pending:
            time.sleep(5)
            server = Server.retrieve(server_id, auth_token)

        tag = self._get_tag(config) if (not force) else None
        result = server.get_pki(tag)

        if result is not PKI.NOT_MODIFIED:
            pki = cast(PKI, result)

            if pki.entity is not None:
                self._handle_pki(result, config, out, post_hook)
                print("Certificates saved to {}.".format(out), file=self.stdout)
            else:
                print("No certificate available. Request one with req.", file=self.stdout)
        else:
            print("Not modified. Pass -f to download anyway.", file=self.stdout)

    def _get_tag(self, config):
        # type: (ConfigParser) -> str
        try:
            tag = config.get('serverapi', 'pki_tag')
        except NoOptionError:
            tag = None

        return tag

    def _handle_pki(self, pki, config, out, post_hook):
        # type: (PKI, ConfigParser, str, str) -> None
        self._write_pki(pki, out)

        if post_hook is not None:
            returncode = subprocess.call(post_hook, shell=True)
            if returncode != 0:
                raise CommandError("{} exited with status {}".format(post_hook, returncode))

        config.set('serverapi', 'pki_tag', pki.tag)

    def _write_pki(self, pki, out):
        # type: (PKI, str) -> None
        with open(os.path.join(out, 'anchor.pem'), 'w') as f:
            f.write(pki.anchor.pem)

        with open(os.path.join(out, 'client_ca.pem'), 'w') as f:
            f.write(pki.client_ca.pem)

        with open(os.path.join(out, 'server.pem'), 'w') as f:
            f.write(pki.entity.pem)
            f.write(pki.server_ca.pem)

        with open(os.path.join(out, 'crl_urls.txt'), 'w') as f:
            for crl in pki.crls:
                print(crl, file=f)
