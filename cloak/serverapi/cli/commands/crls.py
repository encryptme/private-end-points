from __future__ import absolute_import, division, print_function, unicode_literals

from hashlib import sha1
import os
import os.path
import subprocess

from asn1crypto import pem
import requests
from six.moves.configparser import ConfigParser, NoOptionError  # noqa
from six.moves.urllib.parse import urlsplit
from typing import Any, List, Dict, Tuple  # noqa

from ._base import BaseCommand, CommandError


CONFIG_SECTION = 'serverapi:crls'


class Command(BaseCommand):
    brief = "Refresh CRLs"
    description = """
        Downloads updated copies of one or more CRLs. This doesn't interact
        with the API, but it's provided as a convenience. This saves ETags to
        the config file to minimize traffic and detect changes.
    """

    def add_arguments(self, parser, group):
        group.add_argument('-i', '--infile', help="Path to a file with URLs (one per line).")
        group.add_argument('-o', '--out', default=os.getcwd(), help="Where to download the CRLs. Defaults to the current directory.")
        group.add_argument('-f', '--format', dest='fmt', choices=['der', 'pem'], default='pem', help="The format to output. [%(default)s]")
        group.add_argument('-p', '--post-hook', help="Command to run if any CRLs were updated. This will be run in a shell.")
        group.add_argument('urls', nargs='*', metavar='url', help="A CRL to download.")

    def handle(self, config, infile, out, fmt, post_hook, urls, **options):
        if not config.has_section(CONFIG_SECTION):
            config.add_section(CONFIG_SECTION)

        if infile is not None:
            with open(infile, 'rt') as f:
                urls.extend(url.strip() for url in f)

        any_updated = False
        for url in urls:
            updated = self._fetch_crl(config, url, out, fmt)
            any_updated = any_updated or updated

        if any_updated and (post_hook is not None):
            returncode = subprocess.call(post_hook, shell=True)
            if returncode != 0:
                raise CommandError("{} exited with status {}".format(post_hook, returncode))

    def _fetch_crl(self, config, url, out, fmt):
        # type: (ConfigParser, str, str, str) -> bool
        updated = False

        url_hash = sha1(url.encode('utf-8')).hexdigest()
        headers = {}  # type: Dict[str, str]

        try:
            etag = config.get(CONFIG_SECTION, url_hash)
        except NoOptionError:
            pass
        else:
            headers = {'If-None-Match': etag}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            crl_name = os.path.basename(urlsplit(url).path)
            crl_name, content = self._format_crl(crl_name, response.content, fmt)
            crl_path = os.path.join(out, crl_name)
            with open(crl_path, 'wb') as f:
                f.write(content)
            print(crl_path, file=self.stdout)
            updated = True

            if 'ETag' in response.headers:
                config.set(CONFIG_SECTION, url_hash, response.headers['ETag'])
        elif response.status_code == 304:
            pass
        else:
            print("Error {} downloading {}: {}".format(
                response.status_code, url, response.content
            ), file=self.stderr)

        return updated

    def _format_crl(self, name, content, fmt):
        # type: (str, bytes, str) -> Tuple[str, bytes]
        """
        Forces a CRL to DER or PEM.

        name: The original name of the downloaded CRL.
        content: The CRL contents.
        fmt: 'der' or 'pem'.

        Returns the updated name and content: (name, content),

        """
        base, ext = os.path.splitext(name)
        is_pem = pem.detect(content)

        if fmt == 'pem':
            ext = '.pem'
            if not is_pem:
                content = pem.armor('X509 CRL', content)
        elif fmt == 'der':
            ext = '.crl'
            if is_pem:
                _, _, content = pem.unarmor(content)

        return (base + ext, content)
