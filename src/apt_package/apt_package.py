import os
import threading
import time
import traceback

from apt_repo import APTRepository

from src.log import status_logger

UBUNTU_DISTRO = "noble"
INITIAL_DISTRO_SSH_VERSION = "SSH-2.0-OpenSSH_9.6p1 Ubuntu-4ubuntu0.3"


class AptPackage(threading.Thread):

    version: str

    def __init__(self):
        super().__init__(daemon=True)
        self.start()
        self.refresh_version()

    def run(self):
        while True:
            time.sleep(24 * 60 * 60)     # 24h
            try:
                self.refresh_version()
            except Exception:
                traceback.print_exc()

    def refresh_version(self):
        self.version = self.get_updated_version()
        # This is the only method that writes to self.version,
        # so reads should be thread-safe.

        status_logger.info(f"Updated apt_package.version to {self.version}")

    def get_updated_version(self):
        # Reference on versioning scheme: https://man.archlinux.org/man/deb-version.7#debian-revision
        base_version_components = INITIAL_DISTRO_SSH_VERSION.split("-")[:-1]
        version_components = (*base_version_components, self.get_updated_revision())
        return "-".join(version_components)

    def get_updated_revision(self):
        if os.environ.get("DEV") == "1":
            # Speedup: don't download at every start in development
            return "9ubuntu9.9"

        # There are no signature checks, so use https:
        url = "https://mirrors.edge.kernel.org/ubuntu"
        dist = f"{UBUNTU_DISTRO}-updates"
        components = ("main",)

        try:
            repo = APTRepository(url, dist, components)
            package = repo.get_packages_by_name("openssh-server")[0]
            debian_revision: str = package.version.split("-")[-1]
        except Exception as e:
            # Probably a network error,
            # but the apt_repo package instead of raising just returns None somewhere.
            msg = "Failed to obtain version, can't start ssh server without it."
            raise RuntimeError(msg) from e
            # On startup, this is the main thread so the whole program will crash.
            # docker-compose will restart the container and retry first very quickly,
            # and then every 1min.
        else:
            return debian_revision


apt_package = AptPackage()  # Singleton


def get_updated_ssh_version():
    # Thread-safe read
    local_version = apt_package.version
    if local_version:
        return local_version
    msg = "Empty updated_ssh_version"
    raise RuntimeError(msg)
