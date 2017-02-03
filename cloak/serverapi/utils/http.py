from __future__ import absolute_import, division, print_function, unicode_literals

from requests import Session
from six.moves.urllib.parse import urljoin

import cloak.serverapi as defaults
from cloak.serverapi.errors import ServerApiError


session = Session()


def get(path, api_version=None, **kwargs):
    return _call('GET', path, api_version, **kwargs)


def post(path, api_version=None, **kwargs):
    return _call('POST', path, api_version, **kwargs)


def _call(method, path, api_version=None, **kwargs):
    if api_version is None:
        api_version = defaults.api_version

    url = urljoin(defaults.base_url, path)

    headers = kwargs.setdefault('headers', {})
    if api_version is not None:
        headers['X-Cloak-API-Version'] = api_version

    if None not in (defaults.server_id, defaults.auth_token):
        kwargs.setdefault('auth', (defaults.server_id, defaults.auth_token))

    if method == 'GET':
        response = session.get(url, **kwargs)
    elif method == 'POST':
        response = session.post(url, **kwargs)
    else:
        raise NotImplementedError()

    if response.status_code not in xrange(200, 400):
        raise ServerApiError(response)

    return response
