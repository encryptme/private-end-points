from __future__ import absolute_import, division, print_function, unicode_literals

from hashlib import sha1
import os.path
import subprocess

import requests
from six.moves.configparser import NoOptionError
from six.moves.urllib.parse import urlsplit

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
        group.add_argument('-o', '--out', help="Where to download the CRLs. Defaults to the current directory.")
        group.add_argument('-p', '--post-hook', help="Command to run if any CRLs were updated. This will be run in a shell.")
        group.add_argument('urls', nargs='+', metavar='url', help="A CRL to download.")

    def handle(self, config, out, post_hook, urls, **options):
        if not config.has_section(CONFIG_SECTION):
            config.add_section(CONFIG_SECTION)

        any_updated = False
        for url in urls:
            updated = self._fetch_crl(config, url, out)
            any_updated = any_updated or updated

        if any_updated and (post_hook is not None):
            returncode = subprocess.call(post_hook, shell=True)
            if returncode != 0:
                raise CommandError("{} exited with status {}".format(post_hook, returncode))

    def _fetch_crl(self, config, url, out):
        updated = False

        url_hash = sha1(url.encode('utf-8')).hexdigest()
        headers = {}

        try:
            etag = config.get(CONFIG_SECTION, url_hash)
        except NoOptionError:
            pass
        else:
            headers = {'If-None-Match': etag}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            crl_name = os.path.basename(urlsplit(url).path)
            crl_path = os.path.join(out, crl_name)
            with open(crl_path, 'wb') as f:
                f.write(response.content)
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
