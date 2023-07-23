import contextlib
import logging
import re
from base64 import b64decode

import paramiko

whoami_server = {
    "host": "whoami.filippo.io",
    "key": "whoami.filippo.io ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBYBzfSibeNCydOnOYXdIBB9e3F1guVbwnbQQ9BdtkmH",
}

logging_level = logging.INFO

username="user"
class MyAuthHandler(paramiko.auth_handler.AuthOnlyHandler):
    def auth_publickey(self, username, _key):
        # All I've got is the pubkey, without the private part,
        # so I can't use Paramiko's implementation that immediately signs.
        #
        # So this is a hybrid between
        # https://github.com/paramiko/paramiko/blob/3.2.0/paramiko/auth_handler.py#L1044
        # and
        # https://github.com/openssh/openssh-portable/blob/V_9_3_P2/sshconnect2.c#L1516

        # TODO
        algorithm = "ssh-rsa"
        pubk = "AAAAB3NzaC1yc2EAAAADAQABAAABAQCoQ9S7V+CufAgwoehnf2TqsJ9LTsu8pUA3FgpS2mdVwcMcTs++8P5sQcXHLtDmNLpWN4k7NQgxaY1oXy5e25x/4VhXaJXWEt3luSw+Phv/PB2+aGLvqCUirsLTAD2r7ieMhd/pcVf/HlhNUQgnO1mupdbDyqZoGD/uCcJiYav8i/V7nJWJouHA8yq31XS2yqXp9m3VC7UZZHzUsVJA9Us5YqF0hKYeaGruIHR2bwoDF9ZFMss5t6/pzxMljU/ccYwvvRDdI7WX4o4+zLuZ6RWvsU6LGbbb0pQdB72tlV41fSefwFsk4JRdKbyV3Xjf25pV4IXOTcqhy+4JTB/jXxrF"

        def finish(m: paramiko.Message):
            m.add_boolean(b=False)
            m.add_string(algorithm)
            m.add_string(b64decode(pubk))

        return self.send_auth_request(username, "publickey", finish)

    def _parse_userauth_info_request(self, m):
        # This method is actually _parse_60
        if __debug__:
            assert paramiko.common.MSG_USERAUTH_INFO_REQUEST == 60  # noqa: S101, PLR2004
            assert paramiko.common.MSG_USERAUTH_PK_OK == 60         # noqa: S101, PLR2004
        # But it's not implemented for publickey:
        if self.auth_method == "publickey":
            return self._parse_userauth_pk_ok(m)
        return super()._parse_userauth_info_request(m)

    def _parse_userauth_pk_ok(self, _m):
        msg = (
            "Server is interested in this public key,"
            " but I can't continue because I don't have the private part."
        )
        raise RuntimeError(msg)
        # Idea: probe servers with keys from https://github.com/_.keys  :frog:


class MyTransport(paramiko.transport.ServiceRequestingTransport):
    def get_auth_handler(self):
        return MyAuthHandler(self)


class MyAuthStrategy:
    def authenticate(self, transport):
        # This is expected to fail:
        with contextlib.suppress(paramiko.AuthenticationException):
            transport.auth_publickey(username, None)########

        # This is expected to succeed:
        transport.auth_interactive_dumb(username)########


def setup_logger():
    logging.basicConfig(
        format="%(levelname)s:%(name)s\t%(message)s",
        level=logging_level,
    )

def add_host_key_entry(client):
    entry = paramiko.hostkeys.HostKeyEntry.from_line(whoami_server["key"])
    client.get_host_keys()._entries.append(entry)  # noqa: SLF001

def do_ssh():
    with paramiko.SSHClient() as client:
        add_host_key_entry(client)
        client.connect(
            whoami_server["host"],
            timeout=10,
            transport_factory=MyTransport,
            auth_strategy=MyAuthStrategy(),
        )
        chan = client.get_transport().open_session(timeout=10)
        chan.settimeout(10)     # Improvement: implement a single timeout up to the "return"
        chan.get_pty()
        response_data = chan.makefile().read()
        return response_data.decode("utf-8")

def get_github(res):
    no_match_pat = re.compile(r"but\W+got\W+no\W+match")
    if no_match_pat.search(res):
        return None

    match_pat = re.compile(r"Hello (.+)!.+https://github\.com/(.+)\.keys", re.DOTALL)
    if match := match_pat.search(res):
        return {
            "name": match.group(1),
            "user": match.group(2),
        }

    logging.warning(f"Undecided response:\n{res}")
    msg = "Could not decide if response was a match or not"
    raise ValueError(msg)

setup_logger()
res = do_ssh()
print(get_github(res))  # noqa: T201
