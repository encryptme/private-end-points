"""
A mocking layer for the API.
"""

from base64 import b64decode
import io
import json
import random
import string

import requests
from six.moves import xrange
from six.moves.urllib.parse import parse_qs, urljoin, urlparse
from typing import Any, Dict  # noqa

from cloak.serverapi.utils import http
from cloak.serverapi.utils.encoding import force_text


mixed_alphabet = string.ascii_letters + string.digits
lower_alphabet = string.ascii_lowercase + string.digits


class MockSession:
    """
    Maintains the API state over a series of serverapi requests.

    An instance of this class can stand in for
    cloak.serverapi.utils.http.session.

    """
    def __init__(self, def_target_id):
        # type: () -> None
        self.session = requests.Session()

        self.server_id = None               # type: str
        self.auth_token = None              # type: str
        self.api_version = None             # type: str
        self.name = None                    # type: str
        self.auth_token = None              # type: str
        self.target_id = None               # type: str
        self.def_target_id = def_target_id  # type: str

        self.csr = None                     # type: str
        self.pki_tag = None                 # type: str

    def get(self, url, **kwargs):
        # type: (str, **Any) -> requests.Response
        request = requests.Request('GET', url, **kwargs)
        prepped = self.session.prepare_request(request)

        path = self._url_path(url)
        if path == 'server/':
            response = self._get_server(prepped)
        elif path == 'server/pki/':
            response = self._get_server_pki(prepped)
        else:
            raise NotImplementedError(('GET', path))

        return response

    def post(self, url, **kwargs):
        # type: (str, **Any) -> requests.Response
        request = requests.Request('POST', url, **kwargs)
        prepped = self.session.prepare_request(request)

        path = self._url_path(url)
        if path == 'servers/':
            response = self._post_servers(prepped)
        elif path == 'server/':
            response = self._post_server(prepped)
        elif path == 'server/csr/':
            response = self._post_server_csr(prepped)
        else:
            raise NotImplementedError(('POST', path))

        return response

    #
    # Implementation
    #

    def _get_server(self, request):
        # type: (requests.PreparedRequest) -> requests.Response
        if self._authenticate(request):
            result = self._server_result()
            response = self._response(request, 200, result)
        else:
            response = self._response(request, 401)

        return response

    def _get_server_pki(self, request):
        # type: (requests.PreparedRequest) -> requests.Response
        query = parse_qs(force_text(urlparse(request.url).query))

        try:
            tag = query['tag'][0]
        except LookupError:
            tag = None

        if self._authenticate(request):
            result = None  # type: Dict[str, Any]

            if self.csr is None:
                result = {
                    'anchor': None, 'server_ca': None, 'client_ca': None,
                    'entity': None, 'crls': [], 'tag': None,
                }
                response = self._response(request, 200, result)
            elif (tag is not None) and (tag == self.pki_tag):
                response = self._response(request, 304)
            else:
                result = {
                    'anchor': self._cert_result('anchor'),
                    'server_ca': self._cert_result('server_ca'),
                    'client_ca': self._cert_result('client_ca'),
                    'entity': self._cert_result('entity'),
                    'crls': ['http://crl.example.com/server.crl'],
                    'tag': self.pki_tag,
                }
                response = self._response(request, 200, result)
        else:
            response = self._response(request, 401)

        return response

    def _post_servers(self, request):
        # type: (requests.PreparedRequest) -> requests.Response
        data = parse_qs(force_text(request.body))

        # Make sure these exist
        data['auth_token'][0]
        data['name'][0]

        self.server_id = self._public_id('srv')
        self.auth_token = ''.join(random.choice(mixed_alphabet) for i in xrange(20))
        self.api_version = force_text(request.headers['X-Cloak-API-Version'])
        self.name = data['name'][0]
        self.auth_token = data['auth_token'][0]
        self.target_id = self.def_target_id


        result = {
            'server_id': self.server_id,
            'auth_token': self.auth_token,
            'server': self._server_result(),
        }

        return self._response(request, 201, result)

    def _post_server(self, request):
        # type: (requests.PreparedRequest) -> requests.Response
        data = parse_qs(force_text(request.body))

        if 'name' in data:
            self.name = data['name'][0]
        if 'api_version' in data:
            self.api_version = data['api_version'][0]

        return self._response(request, 200, self._server_result())

    def _post_server_csr(self, request):
        # type: (requests.PreparedRequest) -> requests.Response
        data = parse_qs(force_text(request.body))

        if self._authenticate(request):
            self.csr = data['csr'][0]
            self.pki_tag = ''.join(random.choice(mixed_alphabet) for i in xrange(16))
            response = self._response(request, 202)
        else:
            response = self._response(request, 401)

        return response

    #
    # Utils
    #

    def _public_id(self, prefix):
        # type: (str) -> str
        return '{}_{}'.format(prefix, ''.join(random.choice(lower_alphabet) for i in xrange(16)))

    def _url_path(self, url):
        # type: (str) -> str
        base_url = urljoin(http.base_url, '/api/server/')
        if url.startswith(base_url):
            path = url[len(base_url):]
        else:
            path = url

        return path

    def _authenticate(self, request):
        # type: (requests.PreparedRequest) -> bool
        authorization = force_text(request.headers['Authorization'])
        decoded = b64decode(authorization[6:].encode('ascii')).decode('ascii')
        server_id, auth_token = decoded.split(':')

        authenticated = (server_id == self.server_id) and (auth_token == self.auth_token)

        return authenticated

    def _server_result(self):
        # type: () -> Dict[str, Any]
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
        # type: (str, str, str) -> Dict[str, str]
        return {'name': name, 'serial': serial, 'pem': pem}

    def _response(self, request, status, result=None, headers={}):
        # type: (requests.PreparedRequest, int, Any, Dict[str, str]) -> requests.Response
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
