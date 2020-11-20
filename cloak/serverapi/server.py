from base64 import b64encode
import socket

from asn1crypto import keys, pem
from csrbuilder import CSRBuilder
import six
from typing import Tuple, Any, Union  # noqa

from cloak.serverapi.utils import http
from cloak.serverapi.utils.apiresult import ApiResult


# The default API version for registering new servers.
default_api_version = '2017-02-28'


class Server(ApiResult):
    # Populated on instances.
    server_id = None  # type: str
    auth_token = None  # type: str

    #
    # Constructors
    #

    @classmethod
    def register(cls, reg_key, name=None, api_version=default_api_version):
        # type: (str, str, str, str, str) -> Server
        """
        Registers a new server to a team.

        reg_key: Registration key from Encrypt.me
        name: Name of the server. Defaults to the host fqdn.
        api_version: Optional API version. Defaults to the latest version known to
            this package.

        """
        if name is None:
            name = socket.getfqdn()

        data = {
            'auth_token': reg_key,
            'name': name,
        }

        result = http.post('servers/', api_version=api_version, data=data).json()

        server_id = result['server_id']
        auth_token = result['auth_token']
        server_result = result['server']

        return cls(server_id, auth_token, server_result)

    @classmethod
    def retrieve(cls, server_id, auth_token):
        # type: (str, str) -> Server
        """
        Retrieves the state of an existing server.
        """
        result = http.get('server/', auth=(server_id, auth_token)).json()

        return cls(server_id, auth_token, result)

    @classmethod
    def wireguard_peers(cls, server_id, auth_token):
        # type: (str, str) -> Server
        """
        Returns the WireGuard peers to help with self-configuration.
        """
        result = http.get('server/wireguard-peers/', auth=(server_id, auth_token)).json()

        return result

    #
    # Operations
    #

    UPDATABLE = ['name', 'api_version', 'wireguard_public_key']

    def update_server(self, **kwargs):
        # type: (**str) -> None
        """
        Updates simple server properties.

        Valid keyword args: name, api_version, wireguard_public_key

        """
        updates = {
            k: v for k, v in kwargs.items()
            if (k in self.UPDATABLE) and bool(v)
        }

        if len(updates) > 0:
            result = http.post('server/', data=updates, auth=self._api_auth).json()

            # We're a dict, so just replace the contents.
            self.clear()
            self.update(result)

    def request_certificate(self, key_pem):
        # type: (str) -> bool
        """
        Requests a new certificate for this server.

        key_pem: the PEM-encoded private key (byte string).

        Returns True if the request was accepted, raises ServerApiError otherwise.

        """
        der = pem.unarmor(key_pem)[2]
        privkey = keys.PrivateKeyInfo.load(der)

        builder = CSRBuilder(
            {'common_name': six.text_type(self.server_id)},
            privkey.public_key_info
        )
        csr = builder.build(privkey)

        data = {
            'csr': b64encode(csr.dump())
        }

        http.post('server/csr/', data=data, auth=self._api_auth)

        return True

    def get_pki(self, tag=None):
        # type: (str) -> object
        """
        Retrieves the server's current PKI information.

        The PKI object may have a 'tag' property. If so, you can pass this tag
        on subsequent requests to see if anything has changed, like a
        certificate renewal. If not, this will return PKI.NOT_MODIFIED.

        """
        params = {}
        if tag is not None:
            params['tag'] = tag

        response = http.get('server/pki/', params=params, auth=self._api_auth)

        if response.status_code == 304:
            pki = PKI.NOT_MODIFIED
        else:
            pki = PKI(response.json())

        return pki

    #
    # Private
    #

    def __init__(self, server_id, auth_token, *args, **kwargs):
        # type: (str, str, *Any, **Any) -> None
        self.server_id = server_id
        self.auth_token = auth_token

        super().__init__(*args, **kwargs)

    @property
    def _api_auth(self):
        # type: () -> Tuple[str, str]
        return (self.server_id, self.auth_token)


class PKI(ApiResult):
    NOT_MODIFIED = object()
