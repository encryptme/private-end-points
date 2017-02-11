from __future__ import absolute_import, division, print_function, unicode_literals

from .base import TestCase


class RegisterTestCase(TestCase):
    def test_register(self):
        returncode = self.main([
            'register',
            '-e', 'alice@example.com',
            '-p', 'password',
            '-t', 'tgt_z24y7miezisykwi6',
            '-n', 'srv1.team.example.com',
        ])

        self.assertEqual(returncode, 0)
        self.assertEqual(self.session.target_id, 'tgt_z24y7miezisykwi6')
