from __future__ import absolute_import, division, print_function, unicode_literals

from setuptools import setup, find_packages


setup(
    name='cloak-server',
    version='1.0',
    author='Cloak',
    author_email='hello@getcloak.com',
    description="Tool for configuring private Cloak endpoints.",
    license='BSD',
    url='https:/1github.com/bbits/cloak-server',
    install_requires=[
        'asn1crypto>=0.21.0',
        'csrbuilder>=0.10.1',
        'oscrypto>=0.18.0',
        'requests>=2.5.1',
        'six>=1.10.0',
    ],
    packages=find_packages(),
    namespace_packages=['cloak'],
    scripts=['bin/cloak-server'],
    test_suite='cloak.serverapi.tests',
)
