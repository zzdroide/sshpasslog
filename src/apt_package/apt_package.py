import os
import threading
import time
import traceback

from apt_repo import APTRepository  # type: ignore


UBUNTU_DISTRO = 'focal'
INITIAL_DISTRO_SSH_VERSION = 'SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.3'

# Reference on versioning scheme: https://serverfault.com/questions/604541/debian-packages-version-convention/604549#604549

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
        print(f'Updated apt_package.version to {self.version}')

    def get_updated_version(self):
        base_version_components = INITIAL_DISTRO_SSH_VERSION.split('-')[:-1]
        return '-'.join(base_version_components + [self.get_updated_revision()])

    def get_updated_revision(self):
        if os.environ.get('DEV') == '1':
            # Speedup: don't download at every start in development
            return '9ubuntu9.9'

        # There are no signature checks, so use https:
        url = 'https://mirrors.edge.kernel.org/ubuntu'
        dist = f'{UBUNTU_DISTRO}-updates'
        components = ('main',)
        repo = APTRepository(url, dist, components)
        package = repo.get_packages_by_name('openssh-server')[0]
        debian_revision: str = package.version.split('-')[-1]
        return debian_revision


apt_package = AptPackage()  # Singleton

def get_updated_ssh_version():
    return apt_package.version
