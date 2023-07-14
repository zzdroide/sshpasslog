from dataclasses import dataclass
import socketserver

import paramiko

from .logger import LoggingMixin

@dataclass
class MyServer(paramiko.ServerInterface, LoggingMixin):
    client_ip: str
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
        # TODO: save
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
        # TODO: get latest version automatically from https://pypi.org/project/apt-repo/
        self._CLIENT_ID = "OpenSSH_8.2p1 Ubuntu-4ubuntu0.7"
        super().__init__(*args, **kwargs)
        self.add_server_key(MyTransport.host_key)


class ReqHandler(socketserver.BaseRequestHandler, LoggingMixin):
    client_ip: str
    my_server: MyServer
    transport: MyTransport

    def setup(self):
        self.client_ip = self.client_address[0]
        self.log('conn')
        self.my_server = MyServer(self.client_ip)
        self.transport = MyTransport(self.request)

    def handle(self):
        try:
            self.transport.start_server(server=self.my_server)
            chan = self.transport.accept(30)
            assert chan is None     # Client can't open a channel without authenticating
        except (OSError, EOFError):
            pass

    def finish(self):
        self.transport.close()
        self.log('disc')


PORT = 2222

def run_server():
    with socketserver.ThreadingTCPServer(('0.0.0.0', PORT), ReqHandler) as server:
        print(f"Listening on port {PORT}")
        server.serve_forever()
