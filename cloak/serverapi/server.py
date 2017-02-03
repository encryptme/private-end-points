from __future__ import absolute_import, division, print_function, unicode_literals

from base64 import b64encode
import socket

from asn1crypto import keys, pem
from csrbuilder import CSRBuilder
import six

import cloak.serverapi as defaults
from cloak.serverapi.apiresult import ApiResult, SubResult
from cloak.serverapi.utils import http


# The default API version for registering new servers.
default_api_version = '2017-01-01'


def register(email, password, target_id, name=None, api_version=default_api_version):
    """
    Registers a new server to a team.

    email, password: Cloak credentials.
    target_id: Identifies the target to link the server to.
    name: Name of the server. Defaults to the host fqdn.
    api_version: Optional API version. Defaults to the latest version known to
        this package.

    Returns (server_id, auth_token, Server)

    """
    if name is None:
        name = socket.getfqdn()

    data = {
        'email': email,
        'password': password,
        'target': target_id,
        'name': name,
    }

    result = http.post('servers/', api_version=api_version, data=data).json()

    server_id = result['server_id']
    auth_token = result['auth_token']
    server = Server(result['server'])

    return (server_id, auth_token, server)


class Server(ApiResult):
    @classmethod
    def get(cls):
        """ Retrieves the state of an existing server. """
        result = http.get('server/').json()

        return cls(result)

    class Target(ApiResult):
        openvpn = SubResult('openvpn', ApiResult, is_list=True)
        ikev2 = SubResult('ikev2', ApiResult, is_list=True)

    target = SubResult('target', Target)


def request_certificate(key_pem):
    """
    Requests a new certificate for this server.

    key_pem: the PEM-encoded private key (byte string).

    Returns True if the request was accepted, raises ServerApiError otherwise.

    """
    der = pem.unarmor(key_pem)[2]
    privkey = keys.PrivateKeyInfo.load(der)

    builder = CSRBuilder(
        {'common_name': six.text_type(defaults.server_id)},
        privkey.public_key_info
    )
    csr = builder.build(privkey)

    data = {
        'csr': b64encode(csr.dump())
    }

    http.post('server/csr/', data=data)

    return True


class PKI(ApiResult):
    NOT_MODIFIED = object()

    @classmethod
    def get(cls, etag=None):
        """
        Retrieves the server's current PKI information.

        The returned PKI object may have an etag value. If you pass that etag
        subsequently and the server returns a 304, this returns NOT_MODIFIED.

        """
        headers = {}
        if etag is not None:
            headers['If-None-Match'] = etag

        response = http.get('server/pki/', headers=headers)

        if response.status_code == 304:
            pki = cls.NOT_MODIFIED
        else:
            pki = cls(response.json())
            pki.etag = response.headers.get('ETag')

        return pki

    # Populated on instances.
    etag = None

    entity = SubResult('entity', ApiResult)
    intermediates = SubResult('intermediates', ApiResult, is_list=True)
    extras = SubResult('extras', ApiResult, is_list=True)
    anchors = SubResult('anchors', ApiResult, is_list=True)
