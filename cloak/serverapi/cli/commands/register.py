from __future__ import absolute_import, division, print_function, unicode_literals

from getpass import getpass
import socket

from six.moves import input
from six.moves.configparser import NoOptionError

from cloak.serverapi.server import Server

from ._base import BaseCommand, CommandError


class Command(BaseCommand):
    brief = "Register this server to your Encrypt.me team"
    description = """
        Register this server to your Encrypt.me team. You must be an
        administrator of a team and have permission to add new servers. You
        should only need to do this once.
    """
    epilog = "Any options not provided will be prompted for."

    def add_arguments(self, parser, group):
        group.add_argument('-k', '--key', help="Slot registration authorization key")
        group.add_argument('-n', '--name', default=socket.getfqdn(), help="The name of this server. [%(default)s]")

    def handle(self, config, key, name, **options):
        try:
            config.get('serverapi', 'server_id')
        except NoOptionError:
            pass
        else:
            raise CommandError("This server is already registered. If you've unregistered it from your team dashboard, you can delete {}".format(options['config_path']))

        if key is None:
            key = input("Enter your Encrypt.me private end-point slot authorization key: ")

        server = Server.register(key, name)

        config.set('serverapi', 'server_id', server.server_id)
        config.set('serverapi', 'auth_token', server.auth_token)

        print("This server has been registered. The next step is to request a certificate.", file=self.stdout)
