from __future__ import absolute_import, division, print_function, unicode_literals

from functools import partial
import os.path
import shutil
import tempfile

from cloak.serverapi.tests.base import TestCase


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

    def test_register_auto_name(self):
        returncode = self.main([
            'register',
            '-e', 'alice@example.com',
            '-p', 'password',
            '-t', 'tgt_z24y7miezisykwi6',
        ])

        self.assertEqual(returncode, 0)
        self.assertIsNotNone(self.session.name)

    def test_already_registered(self):
        self.main([
            'register',
            '-e', 'alice@example.com',
            '-p', 'password',
            '-t', 'tgt_z24y7miezisykwi6',
        ])
        returncode = self.main([
            'register',
            '-e', 'alice@example.com',
            '-p', 'password',
            '-t', 'tgt_z24y7miezisykwi6',
        ])

        self.assertNotEqual(returncode, 0)


class InfoTestCase(TestCase):
    def test_not_registered(self):
        returncode = self.main(['info'])

        self.assertNotEqual(returncode, 0)

    def test_auth_fail(self):
        self.main([
            'register',
            '-e', 'alice@example.com',
            '-p', 'password',
            '-t', 'tgt_z24y7miezisykwi6',
        ])
        self.session.auth_token = 'bogus'
        returncode = self.main(['info'])

        self.assertNotEqual(returncode, 0)

    def test_print_info(self):
        self.main([
            'register',
            '-e', 'alice@example.com',
            '-p', 'password',
            '-t', 'tgt_z24y7miezisykwi6',
        ])
        returncode = self.main(['info'])

        self.assertEqual(returncode, 0)
        self.assertIn(self.session.server_id, self.stdout.getvalue())


class CSRTestCase(TestCase):
    def test_existing_key(self):
        with tempfile.NamedTemporaryFile('wb', 0) as key_file:
            key_file.write(self.privkey_rsa_2048)

            self.main([
                'register',
                '-e', 'alice@example.com',
                '-p', 'password',
                '-t', 'tgt_z24y7miezisykwi6',
            ])
            returncode = self.main([
                'req', '-k', key_file.name,
            ])

        self.assertEqual(returncode, 0)
        self.assertIsNotNone(self.session.csr)

    def test_new_key(self):
        key_dir = tempfile.mkdtemp()
        self.addCleanup(partial(shutil.rmtree, key_dir))
        key_path = os.path.join(key_dir, 'privkey.pem')

        self.main([
            'register',
            '-e', 'alice@example.com',
            '-p', 'password',
            '-t', 'tgt_z24y7miezisykwi6',
        ])
        returncode = self.main([
            'req', '-k', key_path
        ])

        self.assertEqual(returncode, 0)
        self.assertIsNotNone(self.session.csr)

    def test_bogus_key(self):
        with tempfile.NamedTemporaryFile('wb', 0) as key_file:
            key_file.write(b'bogus')

            self.main([
                'register',
                '-e', 'alice@example.com',
                '-p', 'password',
                '-t', 'tgt_z24y7miezisykwi6',
            ])
            returncode = self.main([
                'req', '-k', key_file.name,
            ])

        self.assertNotEqual(returncode, 0)
        self.assertIsNone(self.session.csr)
        self.assertIn(key_file.name, self.stderr.getvalue())

    def test_bogus_key_path(self):
        key_dir = tempfile.mkdtemp()
        self.addCleanup(partial(shutil.rmtree, key_dir))
        key_path = os.path.join(key_dir, 'bogus', 'privkey.pem')

        self.main([
            'register',
            '-e', 'alice@example.com',
            '-p', 'password',
            '-t', 'tgt_z24y7miezisykwi6',
        ])
        returncode = self.main([
            'req', '-k', key_path
        ])

        self.assertNotEqual(returncode, 0)
        self.assertIsNone(self.session.csr)
        self.assertIn(key_path, self.stderr.getvalue())

    privkey_rsa_2048 = b'-----BEGIN PRIVATE KEY-----\nMIIEwAIBADANBgkqhkiG9w0BAQEFAASCBKowggSmAgEAAoIBAQC7eUdE6MAUMmpF\nku2W9MQnU6V+1q17stlITuNF8zhb4HbplX+Lx8soxnRvY6Hn/uP6IIIi3jNim7vv\nruG53VO/CTSiHgg4wf3rO9Lpy8wIIgQwoUBDrOqsGYlJYK8sc1gEsROA9YdAYSgJ\nrm9luF2bmRho92eFCqzq/2dIgNqT5I2WnwvZSW9cup+BzULfwvXF3QXAzTphGhf+\nsDTdgyd7v3dHRHiyVTva3FICuWgtklDBqcP7GrX/TofPal3/Q6asgHc3UxhWPznY\nFYf73SMpwk7SVFXybW0i8kh0oOk6VVODMThrQnHNpU3sfwqc+ZEFMgFWnOg5sh22\nWbQWZQjdAgMBAAECggEBALg610mlfFScsoiKecb14+lNrv21U6iSuinvtDJicIkB\nTXoAOuYPQdthIrzv6QSGHF0KIzjGqTKHHinM7u/qy0iZcEq8PpIgOTo4gOzWJDv9\nyaZMYE3hGIBlW99rDtocw2tg5Gy/W9ltYJ4a+Ee65OpqiW1layp3sjQBJus+DQ51\nRNAefYOo8UrQGFCzDUgH+QUOCTImbD6sVttDI0DojDM8slPOjdb3ZMRO+esQS0Q/\nzoO3f9dCe0VDBRbgJvRGMs+z/TzqqhSqbZwJDFs3e3ItZyXdz8eaGxfsH4et2PFd\nbAjSuBScbYXQWMTYCNdFgNVQ+5hGkAnolxduAFylnLUCgYEA7DBdp67Q4IpNtuKE\nh1OEQZ5pW7Qi/KpHyqXIsiscsBCgV6wdU38C+KW16gz3Sowc7Wry+cRjJQzF5Cqj\nxw8GcO/+OSqmjOTeHBcPKs2Pp4YnZ+0Bo0jfKSg8/gN/aHi607VavusOLIPzgv6V\nr62RViE5rQHK0waZBG6WQrXn+e8CgYEAyzLcoZcsMOLuk18wszQ77tcoPf9DTsIo\n5hM+NeVzm3fit7LG0TonRC7DZYoBAaQJuxujUXqcu6jTIPeIndRPc2FuWhPQPWzC\nJ/S2dy0WQ5bhvhh7Jw9Ko/2a5SsdP0yxuCwQwIUw1O8zawpWW6xeL1P6O9k01fGr\n6AS4osFg5fMCgYEAjuMzxZ4c/7qsCVhAlR4RhSEw3Cm+gN0DUbW6FQ+/60QjvOaD\nV2AfjA20YEQ31wGs/nUVScVltaRklAS30FVmsCyAwFTtLY/IT3Yj1uFFZzPh4x2f\nQAl1+JA/Ve0Hx0xCupGctKO/j27EgxtBs2Zt5o1zNxc+fSwgpm3AudsS3EECgYEA\nnA7zDhPJd75CFuMrxuYeBYAvQvYyHmHWAWXUCJaxpDx93jGqqnQsRhxYKzrDLRxr\n8Mz4MJKnnyS5Cf+yZ+zwHCA/HWVMMHC/6Onz3TG+gKh3tYSdyNDgtXQHq2viaYQg\nld8Z+pIQf+k6J0JoMr3+FAE+FQrrnkiei3Jcz3sPTWsCgYEAkSSunhic1isgO3xo\nX2G2WjWQwOEVlb2XqK5d7aCNwElAvwtKtU78qJxWVWIiStsRNNyq8pTba9DNH9hy\n+v8hSlVExYFjTm1HlpLqFOu3J60vh0A/76O8QT5Pn3gLs6H8OsIxiIK+edqxbO3K\nCberEki3Q3eUI5fua0HCyZrkP/A=\n-----END PRIVATE KEY-----\n'


class PKITestCase(TestCase):
    def setUp(self):
        super(PKITestCase, self).setUp()

        self.out_path = tempfile.mkdtemp()
        self.server_cert_path = os.path.join(self.out_path, 'server.pem')
        self.hook_path = os.path.join(self.out_path, 'changed.txt')
        self.addCleanup(partial(shutil.rmtree, self.out_path))

    def test_get_empty_pki(self):
        self.main([
            'register',
            '-e', 'alice@example.com',
            '-p', 'password',
            '-t', 'tgt_z24y7miezisykwi6',
        ])
        returncode = self.main([
            'pki', '-o', self.out_path
        ])

        self.assertEqual(returncode, 0)

    def test_get_pki(self):
        with tempfile.NamedTemporaryFile('wb', 0) as key_file:
            key_file.write(self.privkey_rsa_2048)

            self.main([
                'register',
                '-e', 'alice@example.com',
                '-p', 'password',
                '-t', 'tgt_z24y7miezisykwi6',
            ])
            self.main([
                'req', '-k', key_file.name,
            ])
            returncode = self.main([
                'pki', '-o', self.out_path
            ])

        self.assertEqual(returncode, 0)
        self.assertTrue(os.path.exists(self.server_cert_path))

    def test_post_hook(self):
        with tempfile.NamedTemporaryFile('wb', 0) as key_file:
            key_file.write(self.privkey_rsa_2048)

            self.main([
                'register',
                '-e', 'alice@example.com',
                '-p', 'password',
                '-t', 'tgt_z24y7miezisykwi6',
            ])
            self.main([
                'req', '-k', key_file.name,
            ])
            returncode = self.main([
                'pki',
                '--out', self.out_path,
                '--post-hook', 'touch {}'.format(self.hook_path)
            ])

        self.assertEqual(returncode, 0)
        self.assertTrue(os.path.exists(self.server_cert_path))
        self.assertTrue(os.path.exists(self.hook_path))

    def test_post_hook_fail(self):
        with tempfile.NamedTemporaryFile('wb', 0) as key_file:
            key_file.write(self.privkey_rsa_2048)

            self.main([
                'register',
                '-e', 'alice@example.com',
                '-p', 'password',
                '-t', 'tgt_z24y7miezisykwi6',
            ])
            self.main([
                'req', '-k', key_file.name,
            ])
            returncode = self.main([
                'pki',
                '--out', self.out_path,
                '--post-hook', 'false',
            ])

        self.assertNotEqual(returncode, 0)

    def test_not_modified(self):
        with tempfile.NamedTemporaryFile('wb', 0) as key_file:
            key_file.write(self.privkey_rsa_2048)

            self.main([
                'register',
                '-e', 'alice@example.com',
                '-p', 'password',
                '-t', 'tgt_z24y7miezisykwi6',
            ])
            self.main([
                'req', '-k', key_file.name,
            ])
            self.main([
                'pki', '-o', self.out_path
            ])
            os.unlink(self.server_cert_path)

            # Should be a no-op because of the etag.
            returncode = self.main([
                'pki',
                '--out', self.out_path,
                '--post-hook', 'touch {}'.format(self.hook_path)
            ])

        self.assertEqual(returncode, 0)
        self.assertFalse(os.path.exists(self.server_cert_path))
        self.assertFalse(os.path.exists(self.hook_path))

    privkey_rsa_2048 = b'-----BEGIN PRIVATE KEY-----\nMIIEwAIBADANBgkqhkiG9w0BAQEFAASCBKowggSmAgEAAoIBAQC7eUdE6MAUMmpF\nku2W9MQnU6V+1q17stlITuNF8zhb4HbplX+Lx8soxnRvY6Hn/uP6IIIi3jNim7vv\nruG53VO/CTSiHgg4wf3rO9Lpy8wIIgQwoUBDrOqsGYlJYK8sc1gEsROA9YdAYSgJ\nrm9luF2bmRho92eFCqzq/2dIgNqT5I2WnwvZSW9cup+BzULfwvXF3QXAzTphGhf+\nsDTdgyd7v3dHRHiyVTva3FICuWgtklDBqcP7GrX/TofPal3/Q6asgHc3UxhWPznY\nFYf73SMpwk7SVFXybW0i8kh0oOk6VVODMThrQnHNpU3sfwqc+ZEFMgFWnOg5sh22\nWbQWZQjdAgMBAAECggEBALg610mlfFScsoiKecb14+lNrv21U6iSuinvtDJicIkB\nTXoAOuYPQdthIrzv6QSGHF0KIzjGqTKHHinM7u/qy0iZcEq8PpIgOTo4gOzWJDv9\nyaZMYE3hGIBlW99rDtocw2tg5Gy/W9ltYJ4a+Ee65OpqiW1layp3sjQBJus+DQ51\nRNAefYOo8UrQGFCzDUgH+QUOCTImbD6sVttDI0DojDM8slPOjdb3ZMRO+esQS0Q/\nzoO3f9dCe0VDBRbgJvRGMs+z/TzqqhSqbZwJDFs3e3ItZyXdz8eaGxfsH4et2PFd\nbAjSuBScbYXQWMTYCNdFgNVQ+5hGkAnolxduAFylnLUCgYEA7DBdp67Q4IpNtuKE\nh1OEQZ5pW7Qi/KpHyqXIsiscsBCgV6wdU38C+KW16gz3Sowc7Wry+cRjJQzF5Cqj\nxw8GcO/+OSqmjOTeHBcPKs2Pp4YnZ+0Bo0jfKSg8/gN/aHi607VavusOLIPzgv6V\nr62RViE5rQHK0waZBG6WQrXn+e8CgYEAyzLcoZcsMOLuk18wszQ77tcoPf9DTsIo\n5hM+NeVzm3fit7LG0TonRC7DZYoBAaQJuxujUXqcu6jTIPeIndRPc2FuWhPQPWzC\nJ/S2dy0WQ5bhvhh7Jw9Ko/2a5SsdP0yxuCwQwIUw1O8zawpWW6xeL1P6O9k01fGr\n6AS4osFg5fMCgYEAjuMzxZ4c/7qsCVhAlR4RhSEw3Cm+gN0DUbW6FQ+/60QjvOaD\nV2AfjA20YEQ31wGs/nUVScVltaRklAS30FVmsCyAwFTtLY/IT3Yj1uFFZzPh4x2f\nQAl1+JA/Ve0Hx0xCupGctKO/j27EgxtBs2Zt5o1zNxc+fSwgpm3AudsS3EECgYEA\nnA7zDhPJd75CFuMrxuYeBYAvQvYyHmHWAWXUCJaxpDx93jGqqnQsRhxYKzrDLRxr\n8Mz4MJKnnyS5Cf+yZ+zwHCA/HWVMMHC/6Onz3TG+gKh3tYSdyNDgtXQHq2viaYQg\nld8Z+pIQf+k6J0JoMr3+FAE+FQrrnkiei3Jcz3sPTWsCgYEAkSSunhic1isgO3xo\nX2G2WjWQwOEVlb2XqK5d7aCNwElAvwtKtU78qJxWVWIiStsRNNyq8pTba9DNH9hy\n+v8hSlVExYFjTm1HlpLqFOu3J60vh0A/76O8QT5Pn3gLs6H8OsIxiIK+edqxbO3K\nCberEki3Q3eUI5fua0HCyZrkP/A=\n-----END PRIVATE KEY-----\n'


class CRLsTestCase(TestCase):
    """
    Breaking the rules and testing with live CRLs.
    """
    def setUp(self):
        super(CRLsTestCase, self).setUp()

        self.out_path = tempfile.mkdtemp()
        self.crl_path = os.path.join(self.out_path, 'cloak-public-clients.crl')
        self.pem_path = os.path.join(self.out_path, 'cloak-public-clients.pem')
        self.hook_path = os.path.join(self.out_path, 'changed.txt')
        self.addCleanup(partial(shutil.rmtree, self.out_path))

    def test_fetch_crls(self):
        returncode = self.main([
            'crls',
            '--out', self.out_path,
            '--format', 'pem',
            '--post-hook', 'touch {}'.format(self.hook_path),
            'http://crl.getcloak.com/cloak-public-clients.crl',
            'http://crl.getcloak.com/cloak-public-servers.crl',
        ])

        self.assertEqual(returncode, 0)
        self.assertTrue(os.path.exists(self.pem_path))
        self.assertTrue(os.path.exists(self.hook_path))

    def test_crls_noop(self):
        self.main([
            'crls',
            '--out', self.out_path,
            '--format', 'der',
            'http://crl.getcloak.com/cloak-public-clients.crl',
            'http://crl.getcloak.com/cloak-public-servers.crl',
        ])
        returncode = self.main([
            'crls',
            '--out', self.out_path,
            '--format', 'der',
            '--post-hook', 'touch {}'.format(self.hook_path),
            'http://crl.getcloak.com/cloak-public-clients.crl',
            'http://crl.getcloak.com/cloak-public-servers.crl',
        ])

        self.assertEqual(returncode, 0)
        self.assertTrue(os.path.exists(self.crl_path))
        self.assertFalse(os.path.exists(self.hook_path))

    def test_hook_fail(self):
        returncode = self.main([
            'crls',
            '--out', self.out_path,
            '--post-hook', 'false',
            'http://crl.getcloak.com/cloak-public-clients.crl',
            'http://crl.getcloak.com/cloak-public-servers.crl',
        ])

        self.assertNotEqual(returncode, 0)

    def test_bad_url(self):
        url = 'http://crl.getcloak.com/totally-bogus-crl.crl'
        returncode = self.main([
            'crls', '--out', self.out_path, url
        ])

        self.assertEqual(returncode, 0)
        self.assertIn(url, self.stderr.getvalue())


class ConfigsTestCase(TestCase):
    def setUp(self):
        super(ConfigsTestCase, self).setUp()

        self.out_path = tempfile.mkdtemp()
        self.addCleanup(partial(shutil.rmtree, self.out_path))

    def test_configs(self):
        """ Coverage. """
        self.main([
            'register',
            '-e', 'alice@example.com',
            '-p', 'password',
            '-t', 'tgt_z24y7miezisykwi6',
        ])
        returncode = self.main([
            'configs',
            '--out', self.out_path,
        ])

        self.assertEqual(returncode, 0)
