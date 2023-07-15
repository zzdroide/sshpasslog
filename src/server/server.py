import socketserver
import threading

import paramiko

from src import apt_package
from src.country import ip2country
from src import db
from src.logger import LoggingMixin


class MyServer(paramiko.ServerInterface, LoggingMixin):
    client_ip_addr: str
    client_ip_country: str

    def __init__(self, src: 'ReqHandler'):
        self.client_ip_addr = src.client_ip_addr
        self.client_ip_country = src.client_ip_country

    username_printed = False

    def get_banner(self):
        # return ("\ndo not type your password here\n\n", "en-US")
        return ("\n  ಠ_ಠ\n\n", "en-US")

    def get_allowed_auths(self, username):
        if not self.username_printed:
            self.log('user', username)
            self.username_printed = True

        return "password,publickey"

    def check_auth_password(self, username, password):
        self.log('pass', f'{username}:{password}')
        db.record_pass(username, password, self.client_ip_addr, self.client_ip_country)
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        self.log('pub', f'{username} {key.fingerprint}')
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        # Client can't open a channel without authenticating
        raise AssertionError("never reached")


class MyTransport(paramiko.Transport):
    # @static
    host_key = paramiko.RSAKey.generate(bits=2048)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.local_version = apt_package.get_updated_ssh_version()
        self.add_server_key(MyTransport.host_key)


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
            negotiated = event.wait(ReqHandler.NEG_TIMEOUT)
            if not negotiated:
                return

            chan = self.transport.accept(ReqHandler.AUTH_TIMEOUT)
            assert chan is None     # Client can't open a channel without authenticating

        except (OSError, EOFError):
            pass

    def finish(self):
        self.transport.close()
        self.log('disc')


PORT = 2222

def run():
    with socketserver.ThreadingTCPServer(('0.0.0.0', PORT), ReqHandler) as server:
        print(f"Listening on port {PORT}")
        server.serve_forever()
