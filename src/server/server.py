import logging
import socketserver
import threading
from pathlib import Path

import paramiko

from src import apt_package, db
from src.country import ip2country
from src.log import LoggingMixin, log_exceptions, logger

VERSION_STR_PREFIX_LEN = len('SSH-2.0-')


class MyServer(paramiko.ServerInterface, LoggingMixin):
    client_ip_addr: str
    client_ip_country: str

    username_printed: bool

    def __init__(self, src: 'ReqHandler'):
        self.client_ip_addr = src.client_ip_addr
        self.client_ip_country = src.client_ip_country

        self.username_printed = False

    @log_exceptions()
    def get_banner(self):
        # return ("\ndo not type your password here\n\n", "en-US")
        return ("\n  ಠ_ಠ\n\n", "en-US")

    def on_got_username(self, username: str):
        """This makes possible to print the bare username before a password is sent."""
        if not self.username_printed:
            self.log('user', username)
            self.username_printed = True

    @log_exceptions()
    def get_allowed_auths(self, username):
        self.on_got_username(username)
        return "password,publickey"

    @log_exceptions()
    def check_auth_none(self, username):
        self.on_got_username(username)
        return paramiko.AUTH_FAILED

    @log_exceptions()
    def check_auth_password(self, username, password):
        self.log('pass', f'{username}:{password}')
        self.username_printed = True
        db.record_pass(username, password, self.client_ip_addr, self.client_ip_country)
        return paramiko.AUTH_FAILED

    @log_exceptions()
    def check_auth_publickey(self, username, key):
        self.log('pub', f'{username} {key.get_base64()}')
        self.username_printed = True
        return paramiko.AUTH_FAILED

    @log_exceptions()
    def check_channel_request(self, kind, chanid):
        # Client can't open a channel without authenticating
        msg = 'never reached'
        raise AssertionError(msg)


class MyTransport(paramiko.Transport):
    server_keys = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.local_version = apt_package.get_updated_ssh_version()
        self.set_host_keys()

        # Stack traces of clients timing out are just spam, so discard ERROR level logs:
        self.logger.setLevel(logging.CRITICAL)

    def set_host_keys(self):
        # Cache:
        if MyTransport.server_keys is None:
            # Load them, once. Paramiko's idea was to execute this on every new request??
            # (On multiple simultaneous first connections, for example by running "ssh-keyscan -p2222 localhost",
            # this will run more than once. But who cares.)
            base_dir = Path('host_keys/etc/ssh/')
            keys = (
                paramiko.RSAKey.from_private_key_file(base_dir / 'ssh_host_rsa_key'),
                paramiko.ECDSAKey.from_private_key_file(base_dir / 'ssh_host_ecdsa_key'),
                paramiko.Ed25519Key.from_private_key_file(base_dir / 'ssh_host_ed25519_key'),
            )
            for k in keys:
                self.add_server_key(k)
            MyTransport.server_keys = self.server_key_dict

        self.server_key_dict = MyTransport.server_keys


class ReqHandler(socketserver.BaseRequestHandler, LoggingMixin):
    NEG_TIMEOUT = 15
    AUTH_TIMEOUT = 30

    client_ip_addr: str
    client_ip_country: str

    my_server: MyServer
    transport: MyTransport

    def setup(self):
        self.client_ip_addr = self.client_address[0]
        self.client_ip_country = ip2country(self.client_ip_addr)
        self.log('conn')
        self.my_server = MyServer(self)
        self.transport = MyTransport(self.request)

    def handle(self):
        try:
            event = threading.Event()
            self.transport.start_server(event=event, server=self.my_server)
            event.wait(ReqHandler.NEG_TIMEOUT)

            if self.transport.remote_version:
                client_ver = self.transport.remote_version[VERSION_STR_PREFIX_LEN:]
                self.log('cli', client_ver)

            self.transport.join(ReqHandler.AUTH_TIMEOUT)

        except (OSError, EOFError):
            pass

    def finish(self):
        self.transport.close()
        self.log('disc')


PORT = 2222

def run():
    with socketserver.ThreadingTCPServer(('0.0.0.0', PORT), ReqHandler) as server:  # noqa: S104
        logger.info(f"Listening on port {PORT}")
        server.serve_forever()
