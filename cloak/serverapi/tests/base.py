from functools import partial
import io
import os
from tempfile import NamedTemporaryFile
import unittest

import six
from unittest import mock

from cloak.serverapi.cli.main import main, get_config
from cloak.serverapi.tests.mock import MockSession


class TestCase(unittest.TestCase):
    def_target_id = 'tgt_z24y7miezisykwi6'

    def setUp(self):
        super().setUp()

        # Capture stdio.
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

        # Tests can check on our current state here.
        self.session = MockSession(def_target_id=self.def_target_id)

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
        self.stdout.close()
        self.stderr.close()

    def main(self, argv):
        return main(argv, self.stdout, self.stderr)

    def get_config(self):
        return get_config()
