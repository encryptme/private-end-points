"""
A mocking layer for the API.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from base64 import b64decode
import io
import json
import random
import string

import requests
from six.moves import xrange
from six.moves.urllib.parse import parse_qs

import cloak.serverapi as defaults


mixed_alphabet = string.ascii_letters + string.digits
lower_alphabet = string.ascii_lowercase + string.digits


class MockSession(object):
    """
    Maintains the API state over a series of serverapi requests.

    An instance of this class can stand in for
    cloak.serverapi.utils.http.session.

    """
    def __init__(self):
        self.session = requests.Session()

        self.server_id = None
        self.auth_token = None
        self.api_version = None
        self.name = None
        self.target_id = None

        self.csr = None
        self.pki_etag = None

    def get(self, url, **kwargs):
        request = requests.Request('GET', url, **kwargs)
        request = self.session.prepare_request(request)

        path = self._url_path(url)
        if path == 'server/':
            response = self._get_server(request)
        elif path == 'server/pki/':
            response = self._get_server_pki(request)
        else:
            raise NotImplementedError(('GET', path))

        return response

    def post(self, url, **kwargs):
        request = requests.Request('POST', url, **kwargs)
        request = self.session.prepare_request(request)

        path = self._url_path(url)
        if path == 'servers/':
            response = self._post_servers(request)
        elif path == 'server/csr/':
            response = self._post_server_csr(request)
        else:
            raise NotImplementedError(('POST', path))

        return response

    #
    # Implementation
    #

    def _get_server(self, request):
        if self._authenticate(request):
            result = self._server_result()
            response = self._response(request, 200, result)
        else:
            response = self._response(request, 401)

        return response

    def _get_server_pki(self, request):
        if self._authenticate(request):
            if request.headers.get('If-None-Match', '') == self.pki_etag:
                response = self._response(request, 304)
            elif self.csr is None:
                result = {
                    'entity': None, 'intermediates': [], 'extras': [],
                    'anchors': [], 'crls': [],
                }
                response = self._response(request, 200, result)
            else:
                result = {
                    'entity': self._cert_result('entity'),
                    'intermediates': [
                        self._cert_result('intermediate1'),
                        self._cert_result('intermediate2'),
                    ],
                    'extras': [
                        self._cert_result('extra1'),
                    ],
                    'anchors': [
                        self._cert_result('anchor1'),
                    ],
                    'crls': [
                        'http://crl.example.com/server.crl'
                    ],
                }
                headers = {'ETag': self.pki_etag}
                response = self._response(request, 200, result, headers=headers)
        else:
            response = self._response(request, 401)

        return response

    def _post_servers(self, request):
        data = parse_qs(request.body)

        self.server_id = self._public_id('srv')
        self.auth_token = ''.join(random.choice(mixed_alphabet) for i in xrange(20))
        self.api_version = request.headers['X-Cloak-API-Version']
        self.name = data['name'][0]
        self.target_id = data['target'][0]

        # Make sure these exist
        data['email'][0]
        data['password'][0]

        result = {
            'server_id': self.server_id,
            'auth_token': self.auth_token,
            'server': self._server_result(),
        }

        return self._response(request, 201, result)

    def _post_server_csr(self, request):
        data = parse_qs(request.body)

        if self._authenticate(request):
            self.csr = data['csr'][0]
            self.pki_etag = ''.join(random.choice(mixed_alphabet) for i in xrange(16))
            response = self._response(request, 202)
        else:
            response = self._response(request, 401)

        return response

    #
    # Utils
    #

    def _public_id(self, prefix):
        return '{}_{}'.format(prefix, ''.join(random.choice(lower_alphabet) for i in xrange(16)))

    def _url_path(self, url):
        if url.startswith(defaults.base_url):
            path = url[len(defaults.base_url):]
        else:
            path = url

        return path

    def _authenticate(self, request):
        authorization = request.headers['Authorization']
        decoded = b64decode(authorization[6:].encode('ascii')).decode('ascii')
        server_id, auth_token = decoded.split(':')

        authenticated = (server_id == self.server_id) and (auth_token == self.auth_token)

        return authenticated

    def _server_result(self):
        """ Hard-coded example server result structure. """
        return {
            'server_id': self.server_id,
            'name': self.name,
            'api_version': self.api_version,
            'target': {
                'target_id': self.target_id,
                'name': 'team.example.com',
                'openvpn': [
                    {'fqdn': 'team.example.com', 'proto': 'udp', 'port': 443, 'cipher': 'AES-CBC-256', 'digest': 'SHA256'},
                    {'fqdn': 'team.example.com', 'proto': 'tcp', 'port': 443, 'cipher': 'AES-CBC-256', 'digest': 'SHA256'},
                ],
                'ikev2': [
                    {'fqdn': 'team.example.com', 'server_id': 'team.example.com', 'client_ca_dn': 'O=Cloak, OU=Teams, CN=Example Clients'},
                ]
            },
            'csr_pending': False,
        }

    def _cert_result(self, name='test', serial='012345', pem='<pem>'):
        return {'name': name, 'serial': serial, 'pem': pem}

    def _response(self, request, status, result=None, headers={}):
        response = requests.Response()
        response.status_code = status
        response.url = request.url

        if result is not None:
            response.raw = io.BytesIO(json.dumps(result).encode('utf-8'))
            response.encoding = 'utf-8'
        else:
            response.raw = io.BytesIO(b'')
            response.encoding = 'latin1'

        response.headers.update(headers)

        return response
