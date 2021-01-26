import argparse  # noqa
import sys

from six.moves.configparser import ConfigParser, NoOptionError  # noqa
from typing import Any, Tuple, IO  # noqa

from cloak.serverapi.server import Server  # noqa


class BaseCommand:
    """
    Base class for cloak-server CLI commands.

    To add a new command:

        1. Add a new module next to this one. The name of the module is the
           name of the command.
        2. Import this class and subclass it as Command.
        3. Override add_arguments() if you want to add any arguments. Override
           handle() to execute the command.
        4. Add the command to the list at the top of cloak.serverapi.cli.main.

    All commands MUST send output to self.stdout and self.stderr. This is
    important for testing and to properly support the --quiet flag.

    """
    brief = None  # type: str
    description = None  # type: str
    epilog = None  # type: str

    def add_arguments(self, parser, group):
        # type: (argparse.ArgumentParser, argparse._ArgumentGroup) -> None
        """
        Subclasses should add arguments here.

        parser: The ArgumentParser.
        group: An argument group named for the command.

        Normally you'll add arguments to the group, but you can add them to the
        parser or create your own groups if you prefer.

        """

    def handle(self, config, **options):
        # type: (ConfigParser, **Any) -> None
        """
        Subclasses implement this to execute the command.

        config: A ConfigParser object with our current configuration. If you
            modify the configuration, the changes will be saved when we're
            done.
        options: Command arguments.

        """
        raise NotImplementedError()

    #
    # Utils
    #

    def _require_credentials(self, config):
        # type: (ConfigParser) -> Tuple[str, str]
        """
        Returns (server_id, auth_token) from our config file.

        If the server is not registered, this will raise a CommandError.

        """
        try:
            server_id = config.get('serverapi', 'server_id')
        except NoOptionError:
            raise CommandError("This server is not registered. Use the 'register' command to link it to your team.")

        try:
            auth_token = config.get('serverapi', 'auth_token')
        except NoOptionError:
            raise CommandError("The config file is missing the authentication token. You may need to re-register the server.")

        return (server_id, auth_token)

    def _print_server(self, server):
        # type: (Server) -> None
        """
        Prints information in a Server instance to stdout.
        """
        target = server.target

        print("Target: {} ({})".format(target.name, target.target_id), file=self.stdout)
        print("Server: {} ({})".format(server.name, server.server_id), file=self.stdout)
        print("", file=self.stdout)

        for openvpn in target.openvpn:
            print("OpenVPN: {}  {}/{}  {}/{}".format(
                openvpn.fqdn, openvpn.proto, openvpn.port,
                openvpn.cipher, openvpn.digest
            ), file=self.stdout)

        for ikev2 in target.ikev2:
            print("IKEv2: {}  leftid: {}  rightca: {}".format(
                ikev2.fqdn, ikev2.server_id, ikev2.client_ca_dn
            ), file=self.stdout)

        try:
            for wireguard in target.wireguard:
                print("Wireguard: {}  public_key: {}".format(
                    wireguard.fqdn, wireguard.public_key
                ), file=self.stdout)
        except AttributeError:
            pass

    #
    # Internal
    #

    def __init__(self, stdout=sys.stdout, stderr=sys.stderr):
        # type: (IO[str], IO[str]) -> None
        self.stdout = stdout
        self.stderr = stderr


class CommandError(Exception):
    pass
