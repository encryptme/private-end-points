#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import sys

from setuptools import setup, find_packages


tests_require = []


setup(
    name='cloak-server',
    version='0.3',
    author='Encrypt.me',
    author_email='hello@encrypt.me',
    description="Tool for configuring private Encrypt.me endpoints.",
    license='BSD',
    url='https://github.com/encryptme/private-end-points',

    install_requires=[
        'asn1crypto>=0.21.0,<1.0.0',
        'csrbuilder>=0.10.1',
        'oscrypto>=0.18.0,<1.0.0',
        'requests>=2.5.1',
        'six>=1.10.0',
        'typing',
    ],

    packages=find_packages(),
    namespace_packages=['cloak'],
    scripts=[
        'bin/cloak-server'
    ],

    test_suite='cloak.serverapi.tests',
    tests_require=tests_require,
)
