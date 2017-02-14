from __future__ import absolute_import, division, print_function, unicode_literals

import os.path
import subprocess

from six.moves.configparser import NoOptionError

from cloak.serverapi.server import Server, PKI

from ._base import BaseCommand, CommandError


class Command(BaseCommand):
    brief = "Download current certificates"
    description = "Downloads current certificates and other PKI information."

    def add_arguments(self, parser, group):
        group.add_argument('-o', '--out', help="Where to download the certificates. Defaults to the current directory.")
        group.add_argument('-p', '--post-hook', help="Command to run if the certificates were updated. This will be run in a shell.")

    def handle(self, config, out, post_hook, **options):
        server_id, auth_token = self._require_credentials(config)
        try:
            etag = config.get('serverapi', 'pki_etag')
        except NoOptionError:
            etag = None

        server = Server.retrieve(server_id, auth_token)
        pki = server.get_pki(etag)

        if (pki is not PKI.NOT_MODIFIED) and (pki.entity is not None):
            self._write_pki(pki, out)

            if post_hook is not None:
                returncode = subprocess.call(post_hook, shell=True)
                if returncode != 0:
                    raise CommandError("{} exited with status {}".format(post_hook, returncode))

            config.set('serverapi', 'pki_etag', pki.etag)

    def _write_pki(self, pki, out):
        # type: (PKI, str) -> None
        with open(os.path.join(out, 'server.pem'), 'w') as f:
            f.write(pki.entity.pem)

        with open(os.path.join(out, 'intermediates.pem'), 'w') as f:
            for cert in pki.intermediates:
                f.write(cert.pem)

        with open(os.path.join(out, 'extras.pem'), 'w') as f:
            for cert in pki.extras:
                f.write(cert.pem)

        with open(os.path.join(out, 'anchors.pem'), 'w') as f:
            for cert in pki.anchors:
                f.write(cert.pem)

        with open(os.path.join(out, 'crl_urls.txt'), 'w') as f:
            for crl in pki.crls:
                print(crl, file=f)
