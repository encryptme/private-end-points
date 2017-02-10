from __future__ import absolute_import, division, print_function, unicode_literals

from getpass import getpass
import socket

from cloak.serverapi.server import Server

from .base import BaseCommand, CommandError


class Command(BaseCommand):
    brief = "Register this server to your Cloak team"
    description = """
        Register this server to your Cloak team. You must be an administrator
        of a team and have permission to add new servers. You should only need
        to do this once.
    """
    epilog = "Any options not provided will be prompted for."

    def add_arguments(self, parser, group):
        group.add_argument('-e', '--email', help="Email address of your Cloak account.")
        group.add_argument('-p', '--password', help="Your Cloak password.")
        group.add_argument('-t', '--target', help="The target to associate this server with. Get this from your team dashboard.")
        group.add_argument('-n', '--name', default=socket.getfqdn(), help="The name of this server. [%(default)s]")

    def handle(self, config, email, password, target, name, **options):
        if config.get('serverapi', 'server_id') is not None:
            raise CommandError("This server is already registered. If you've unregistered it from your team dashboard, you can delete {}".format(options['config_path']))

        if email is None:
            email = raw_input("Enter your Cloak email: ")
        if password is None:
            password = getpass("Enter your Cloak password: ")
        if target is None:
            target = raw_input("Enter the target identifier (from the team dashboard): ")

        server = Server.register(email, password, target, name)

        config.set('serverapi', 'server_id', server.server_id)
        config.set('serverapi', 'auth_token', server.auth_token)

        print(server.server_id)
