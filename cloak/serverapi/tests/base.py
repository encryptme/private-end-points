from __future__ import absolute_import, division, print_function, unicode_literals

from functools import partial
import io
import os
from tempfile import NamedTemporaryFile
import unittest

import six
if six.PY3:
    from unittest import mock
else:
    import mock

from cloak.serverapi.cli.main import main
from cloak.serverapi.tests.mock import MockSession


class TestCase(unittest.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()

        # Capture stdio.
        self.stdin = io.StringIO()
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

        # Tests can check on our current state here.
        self.session = MockSession()

        # Intercept HTTP calls to the API.
        patcher = mock.patch('cloak.serverapi.utils.http.session', self.session)
        patcher.start()
        self.addCleanup(patcher.stop)

        # Make a fresh config file for each test.
        config_file = NamedTemporaryFile()
        os.environ['CLOAK_CONFIG'] = config_file.name
        self.addCleanup(partial(self._cleanup_tempfile, config_file))

    def _cleanup_tempfile(self, config_file):
        config_file.close()
        del os.environ['CLOAK_CONFIG']

    def tearDown(self):
        self.stdin.close()
        self.stdout.close()
        self.stderr.close()

    def main(self, argv):
        return main(argv, self.stdin, self.stdout, self.stderr)
