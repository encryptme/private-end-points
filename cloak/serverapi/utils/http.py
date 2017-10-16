"""
A simple HTTP wrapper that manages standard headers and error responses.

Most clients will want to include the 'auth' keyword argument with credentials.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os

import requests
from six.moves import xrange
from six.moves.urllib.parse import urljoin
from typing import Any  # noqa

from cloak.serverapi.errors import ServerApiError


session = requests.Session()


# This can be overridden for test environments.
base_url = 'https://app.encrypt.me/'

# Set this to send the X-Cloak-API-Version with every request. This can still
# be overridden for individual requests.
default_api_version = None  # type: str

container_version = os.environ.get('CONTAINER_VERSION')


def get(path, api_version=None, **kwargs):
    # type: (str, str, **Any) -> requests.Response
    return _call('GET', path, api_version, **kwargs)


def post(path, api_version=None, **kwargs):
    # type: (str, str, **Any) -> requests.Response
    return _call('POST', path, api_version, **kwargs)


def _call(method, path, api_version=None, **kwargs):
    # type: (str, str, str, **Any) -> requests.Response
    url = urljoin(base_url, '/api/server/')
    url = urljoin(url, path)

    headers = kwargs.setdefault('headers', {})
    if api_version is not None:
        headers['X-Cloak-API-Version'] = api_version
    elif default_api_version is not None:
        headers['X-Cloak-API-Version'] = default_api_version
    if container_version:
        headers['X-Cloak-Container-Version'] = container_version

    if method == 'GET':
        response = session.get(url, **kwargs)
    elif method == 'POST':
        response = session.post(url, **kwargs)
    else:
        raise NotImplementedError()

    if response.status_code not in xrange(200, 400):
        raise ServerApiError(response)

    return response
