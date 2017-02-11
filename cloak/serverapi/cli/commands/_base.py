from __future__ import absolute_import, division, print_function, unicode_literals

import sys


class BaseCommand(object):
    brief = None
    description = None
    epilog = None

    def add_arguments(self, parser, group):
        """
        Subclasses should add arguments here.

        parser: The ArgumentParser.
        group: An argument group named for the command.

        Normally you'll add arguments to the group, but you can add them to the
        parser or create your own groups if you prefer.

        """

    def handle(self, config, **options):
        """
        Subclasses implement this to execute the command.

        config: A ConfigParser object with our current configuration. If you
            modify the configuration, the changes will be saved when we're
            done.
        options: Command arguments.

        """

    #
    # Utils
    #

    def _require_credentials(self, config):
        """
        Returns (server_id, auth_token) from our config file.

        If the server is not registered, this will raise a CommandError.

        """
        server_id = config.get('serverapi', 'server_id')
        auth_token = config.get('serverapi', 'auth_token')

        if server_id is None:
            raise CommandError("This server is not registered. Use the 'register' command to link it to your team.")
        if auth_token is None:
            raise CommandError("The config file is missing the authentication token. You may need to re-register the server.")

        return (server_id, auth_token)

    def _print_server(self, server):
        """
        Prints information in a Server instance to stdout.
        """
        target = server.target

        print("Target: {} ({})".format(target.name, target.target_id), file=self.stdout)
        print("Server: {} ({})".format(server.name, server.server_id), file=self.stdout)
        print(file=self.stdout)

        for openvpn in target.openvpn:
            print("OpenVPN: {}  {}/{}  {}/{}".format(
                openvpn.fqdn, openvpn.proto, openvpn.port,
                openvpn.cipher, openvpn.digest
            ), file=self.stdout)

        for ikev2 in target.ikev2:
            print("IKEv2: {}  leftid: {}  rightca: {}".format(
                ikev2.fqdn, ikev2.server_id, ikev2.client_ca_dn
            ), file=self.stdout)

    #
    # Internal
    #

    def __init__(self, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr


class CommandError(Exception):
    pass
