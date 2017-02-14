from __future__ import absolute_import, division, print_function, unicode_literals

import os
import os.path

from typing import Dict  # noqa

from cloak.serverapi.server import Server

from ._base import BaseCommand


class Command(BaseCommand):
    brief = "Generate sample VPN configs."
    description = """
        Generates sample config files for Cloak VPN services. The config files
        include all of the critical settings to interoperate with Cloak
        clients, but you may will want to customize them for your environment.
    """

    def add_arguments(self, parser, group):
        group.add_argument('-o', '--out', dest='dest', default='.', help="Where to generate the configs. Defaults to the current directory.")

    def handle(self, config, dest, **options):
        server_id, auth_token = self._require_credentials(config)

        server = Server.retrieve(server_id, auth_token)

        self._generate_openvpn(server, dest)
        self._generate_strongswan(server, dest)

    def _generate_openvpn(self, server, dest):
        # type: (Server, str) -> None
        path = os.path.join(dest, 'openvpn')
        if not os.path.exists(path):
            os.makedirs(path)

        aux = {}  # type: Dict[str, str]
        for info in server.target.openvpn:
            extras = []
            if info.proto == 'udp':
                aux['subnet'] = '10.137.0.0'
                extras.append('push "explicit-exit-notify"')
            else:
                aux['subnet'] = '10.137.64.0'
                extras.append('tcp-nodelay')
            aux['extras'] = '\n'.join(extras)

            filepath = os.path.join(path, 'cloak-{}.conf'.format(info.proto))
            content = OPENVPN_CONFIG.format(info=info, aux=aux)
            with open(filepath, 'wt') as f:
                f.write(content.strip())

    def _generate_strongswan(self, server, dest):
        # type: (Server, str) -> None
        path = os.path.join(dest, 'strongswan')
        if not os.path.exists(path):
            os.makedirs(path)

        info = server.target.ikev2[0]
        subnet = '10.137.128.0/18'

        with open(os.path.join(path, 'strongswan.conf'), 'wt') as f:
            f.write(STRONGSWAN_CONFIG.strip())

        content = IPSEC_CONFIG.format(info=info, subnet=subnet)
        content = content.replace('#-----', '')
        with open(os.path.join(path, 'ipsec.conf'), 'wt') as f:
            f.write(content.strip())


OPENVPN_CONFIG = """
# These parameters are shared with the clients and must not be changed.
dev tun
proto {info.proto}
port {info.port}
cipher {info.cipher}
auth {info.digest}

# This defines the virtual subnet. We recommend choosing one of the 10.x.0.0/16
# subnets for Cloak. This will then need to be divided into four /18 networks
# for the different protocols.
server {aux[subnet]} 255.255.192.0

# Update these paths to point to the Cloak PKI files.
key /path/to/key.pem
cert /path/to/server.pem
ca /path/to/anchors.pem
extra-certs /path/to/extras.pem
crl-verify /path/to/crls.pem

# You must also supply Diffie-Hellman parameters. We recommend generating your
# own 2048-bit parameters.
dh /path/to/dh2048.pem

# Just to be on the safe side, we'll make sure that only client certificates
# are accepted. Without this, we would accept connections from other servers
# configured with the same PKI.
remote-cert-eku "TLS Web Client Authentication"

# These are some miscellaneous settings that you'll probably want.
keepalive 10 120
{aux[extras]}
"""


STRONGSWAN_CONFIG = """
# https://wiki.strongswan.org/projects/strongswan/wiki/StrongswanConf
charon {
    # You should push DNS servers with public IPs, so that all queries will be
    # routed through the tunnel.
    dns1 = 8.8.8.8
    dns2 = 8.8.4.4

    # https://wiki.strongswan.org/projects/strongswan/wiki/LoggerConfiguration
    syslog {
        daemon {
        }
        auth {
            default = -1
            ike = 0
        }
    }

    # The default strongSwan config is fine for small numbers of clients. For
    # larger numbers of clients, you may need to reconfigure the IKE_SA hash
    # table and/or the thread pool.

    # https://wiki.strongswan.org/projects/strongswan/wiki/IkeSaTable
    #ikesa_table_size = 128
    #ikesa_table_segments = 8

    # https://wiki.strongswan.org/projects/strongswan/wiki/JobPriority
    #threads = 64
    #processor {
    #    priority_threads {
    #        high = 4
    #        medium = 32
    #    }
    #}
}
"""


# strongSwan is finicky about indentation in ipsec.conf. The '#-----' strings
# are placeholders that will be removed.
IPSEC_CONFIG = """
# This can be combined with other connections in ipsec.conf, but most of its
# parameters should not be changed.
#
# https://wiki.strongswan.org/projects/strongswan/wiki/IpsecConf
conn cloak
    keyexchange = ikev2
    ike = aes256gcm128-sha256-ecp521,aes256gcm128-sha256-ecp256,aes256gcm128-sha256-modp4096,aes256gcm128-sha256-modp2048,aes256gcm128-sha384-ecp521,aes256gcm128-sha384-ecp256,aes256gcm128-sha384-modp4096,aes256gcm128-sha384-modp2048,aes256gcm128-sha512-ecp521,aes256gcm128-sha512-ecp256,aes256gcm128-sha512-modp4096,aes256gcm128-sha512-modp2048,aes256-sha256-ecp521,aes256-sha256-ecp256,aes256-sha256-modp4096,aes256-sha256-modp2048,aes256-sha384-ecp521,aes256-sha384-ecp256,aes256-sha384-modp4096,aes256-sha384-modp2048,aes256-sha512-ecp521,aes256-sha512-ecp256,aes256-sha512-modp4096,aes256-sha512-modp2048,aes128gcm128-sha256-ecp521,aes128gcm128-sha256-ecp256,aes128gcm128-sha256-modp4096,aes128gcm128-sha256-modp2048,aes128gcm128-sha384-ecp521,aes128gcm128-sha384-ecp256,aes128gcm128-sha384-modp4096,aes128gcm128-sha384-modp2048,aes128gcm128-sha512-ecp521,aes128gcm128-sha512-ecp256,aes128gcm128-sha512-modp4096,aes128gcm128-sha512-modp2048,aes128-sha256-ecp521,aes128-sha256-ecp256,aes128-sha256-modp4096,aes128-sha256-modp2048,aes128-sha384-ecp521,aes128-sha384-ecp256,aes128-sha384-modp4096,aes128-sha384-modp2048,aes128-sha512-ecp521,aes128-sha512-ecp256,aes128-sha512-modp4096,aes128-sha512-modp2048!
    esp = aes256gcm128-sha256,aes256gcm128-sha384,aes256gcm128-sha512,aes256-sha256,aes256-sha384,aes256-sha512,aes256-sha1,aes128gcm128-sha256,aes128gcm128-sha384,aes128gcm128-sha512,aes128-sha256,aes128-sha384,aes128-sha512,aes128-sha1!
    compress = yes
    fragmentation = yes
    #-----
    left = %defaultroute
    leftid = {info.server_id}
    leftauth = pubkey
    leftcert = server.pem
    leftsendcert = always
    leftsubnet = 0.0.0.0/0
    #-----
    right = %any
    rightid = %
    rightauth = pubkey
    rightca = "{info.client_ca_dn}"
    # Change this if you're using a different virtual subnet.
    rightsourceip = {subnet}
    #-----
    # These aren't critical, but we've provided some sensible defaults.
    dpddelay = 1m
    dpdtimeout = 5m
    dpdaction = clear
    #-----
    auto = add
"""
