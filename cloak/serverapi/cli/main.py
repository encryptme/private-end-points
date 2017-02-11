from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
from importlib import import_module
import os
import os.path
import sys

import six
from six.moves.configparser import RawConfigParser

from cloak.serverapi.cli.commands._base import CommandError
from cloak.serverapi.errors import ServerApiError


COMMANDS = [
    'register',
    'info',
    'req',
    'pki',
]


def main(argv=None, stdin=sys.stdin, stdout=sys.stdin, stderr=sys.stdin):
    returncode = 0

    try:
        args = parse_args(argv, stdin, stdout, stderr)
        config = get_config(args.config_path)

        args.cmd.handle(config=config, **vars(args))

        with open(args.config_path, 'w') as f:
            config.write(f)
    except ServerApiError as e:
        try:
            result = e.response.json()
        except ValueError:
            print(six.text_type(e), file=stderr)
        else:
            for field, errors in result.get('errors').items():
                for error in errors:
                    print("Error:", error['message'], file=stderr)
    except CommandError as e:
        print(six.text_type(e), file=stderr)
        returncode = 1

    return returncode


def parse_args(argv, stdin, stdout, stderr):
    parser = argparse.ArgumentParser(
        prog='cloak-server',
    )
    parser.add_argument(
        '--config', dest='config_path', default=default_config_path(),
        help="Path to config file. [%(default)s]"
    )

    subparsers = parser.add_subparsers(description="Pass -h to one of the subcommands for more information.")
    for name in COMMANDS:
        mod = import_module('.{}'.format(name), 'cloak.serverapi.cli.commands')
        cmd = mod.Command(stdin, stdout, stderr)
        sub = subparsers.add_parser(
            name, help=cmd.brief, description=cmd.description,
            epilog=cmd.epilog
        )
        cmd.add_arguments(sub, sub.add_argument_group(name))
        sub.set_defaults(cmd=cmd)

    args = parser.parse_args(argv)

    return args


def default_config_path():
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
    """
    Returns a ConfigParser with our current configuration.
    """
    config = RawConfigParser(allow_no_value=True)
    config.read([path])

    if not config.has_section('serverapi'):
        config.add_section('serverapi')

    return config
