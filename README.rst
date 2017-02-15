cloak-server
============

A tool for registering private Cloak VPN endpoints.

This is an official client of the Cloak for Teams server API. It's used to
register your own servers with your team account so that you can provision them
as private Cloak servers.

The ``cloak-server-demo`` project ties everything together into a complete
working example, but here we describe the general use of this client.


Setup
-----

This tool maintains a configuration file with credentials and a few other bits
of state. If you run this tool as root, the default location is /etc/cloak.conf.
Otherwise, it will be in ~/.cloak.conf. All commands accept an argument to
override the path to the config file.

.. warning::

    This config file will be both read and written to, so it's important to make
    sure the tool always has access to it. Most likely this means always running
    it under the same effective uid.


Quick start
-----------

The ``cloak-server`` tool can be installed from <a location to be decided>.


Register
~~~~~~~~

The first step is to register your server with your team. To do this, you will
need your Cloak account email and password. Because teams can have multiple
targets (representing subsets of your servers), you'll also need a target
identifier from your team dashboard.

All parameters can be passed to the registration command, or you can let it
prompt you.

    cloak-server register


Certificates
~~~~~~~~~~~~

Now that the server is registered, you need to provision it. The first step is
to request a server certificate:

    cloak-server req --key /path/to/server-key.pem

If the given key does not exist, one will be generated for you. If it does
exist, it must be an RSA key of at least 2048 bits.

If the request is sent successfully, it will appear on your team dashboard. An
administrator must approve the request, entering the PKI password, if necessary.
Once the request has been approved, you can download the server certificate
along with all associated PKI information:

    cloak-server pki --out /path/to/pki/

This will create several files:

    server.pem
      The server certificate followed by intermediates.

    anchors.pem
      The anchor certificate(s) for the private PKI.

    extras.pem
      Any additional certificates of interest, for example CRL signers.

    crl_urls.txt
      A text file with URLs to any certificate revocation lists (CRLs) that we
      need to know about, one per line.

The response to the PKI request includes an ETag, which we can use to detect
changes. This ETag is saved to our config file and sent in subsequent requests
by default. To check for PKI changes, you can periodically run:

    cloak-server pki --out /path/to/pki/ --post-hook cloak-pki-updated.sh

If the post-hook is executed, it most likely means that the server certificate
has been renewed. The post-hook should restart or reload services for the
updated certificates.

The ``pki`` command also takes a ``-f`` argument to ignore the etag and download
a fresh copy of everything.


Revocation
~~~~~~~~~~

Because CRLs are regenerated frequently, the API returns URLs rather than the
contents. As a convenience, we provide a command that will check for updated
CRLs in a manner similar to the ``pki`` command checking for updated
certificates:

    cloak-server crls --out /path/to/crls/ --post-hook cloak-crls-updated.sh $(cat /path/to/crl_urls.txt)

This command uses the config file to store an etag for each URL, so you can run
it fairly frequently.


Configs
~~~~~~~

Cloak servers must run both OpenVPN and strongSwan to serve clients from all
supported platforms. Many of the configuration parameters can be customized for
individual team servers, but a few of them must be agreed upon in advance by the
client and server. This tool provides a command to generate sample VPN configs
that can then be customized to meet your specific needs:

    cloak-server configs --out /path/to/configs/

These config files will include detailed comments indicating which settings can
be changed and which should be left alone.

.. note::

    Each target's key parameters are fixed at creation time. Thus, it's not
    necessary to run this command on every server: for any new target, you can
    run it once and incorporate the result into your own deployment automation.


Development
-----------

To set up a development environment for this project, just create a virtualenv
with any supported version of Python and run ``pip install -e .``.

Run tests in a single virtualenv with ``python setup.py test``. To test in all
supported environments, install and run ``tox``. This will also run a suite of
static analysis tools to detect potential errors and style issues.