from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
from importlib import import_module
import os
import os.path
import sys

import six
from six.moves.configparser import RawConfigParser
from typing import IO  # noqa

import cloak.serverapi.utils.http
from cloak.serverapi.cli.commands._base import BaseCommand, CommandError  # noqa
from cloak.serverapi.errors import ServerApiError
from cloak.serverapi.utils.encoding import force_text


COMMANDS = [
    'crls',
    'info',
    'pki',
    'register',
    'req',
]


def main(argv=None, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    # type: (List[str], IO[str], IO[str], IO[str]) -> int
    returncode = 0

    try:
        args = parse_args(argv, stdin, stdout, stderr)
        config = get_config(args.config_path)
        cloak.serverapi.utils.http.base_url = config.get('serverapi', 'base_url')

        args.cmd.handle(config=config, **vars(args))

        with open(args.config_path, 'w') as f:
            config.write(f)
    except ServerApiError as e:
        try:
            result = e.response.json()
        except ValueError:
            message = e.response.text or force_text(e.response.reason)
            print(message, file=stderr)
        else:
            for field, errors in result.get('errors').items():
                for error in errors:
                    print("Error:", error['message'], file=stderr)
        returncode = 1
    except CommandError as e:
        print(six.text_type(e), file=stderr)
        returncode = 1

    return returncode


def parse_args(argv, stdin, stdout, stderr):
    # type: (List[str], IO[str], IO[str], IO[str]) -> argparse.Namespace
    parser = argparse.ArgumentParser(
        prog='cloak-server',
    )
    parser.add_argument(
        '--config', dest='config_path', default=default_config_path(),
        help="Path to config file. [%(default)s]"
    )

    subparsers = parser.add_subparsers(description="Pass -h to one of the subcommands for more information.")
    for name in COMMANDS:
        cmd = None  # type: BaseCommand

        mod = import_module('.{}'.format(name), 'cloak.serverapi.cli.commands')
        cmd = getattr(mod, 'Command')(stdin, stdout, stderr)
        sub = subparsers.add_parser(
            name, help=cmd.brief, description=cmd.description,
            epilog=cmd.epilog
        )
        cmd.add_arguments(sub, sub.add_argument_group(name))
        sub.set_defaults(cmd=cmd)

    args = parser.parse_args(argv)

    return args


def default_config_path():
    # type: () -> str
    """
    Returns the path to our working directory.
    """
    path = os.getenv('CLOAK_CONFIG', None)
    if path is None:
        if os.geteuid() == 0:
            path = '/etc/cloak.conf'
        else:
            path = os.path.expanduser('~/.cloak.conf')

    return path


def get_config(path):
    # type: (str) -> RawConfigParser
    """
    Returns a ConfigParser with our current configuration.
    """
    defaults = {
        'base_url': 'https://www.getcloak.com/',
    }

    config = RawConfigParser(defaults)
    config.read([path])

    if not config.has_section('serverapi'):
        config.add_section('serverapi')

    return config
