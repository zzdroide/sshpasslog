import threading
import time
import traceback

from ip3country import CountryLookup    # type: ignore
import requests


class Country(threading.Thread):
    """
    A class to obtain the country from an IP, with the `ip2country` method.

    Create one instance only, as it starts a thread to periodically update data.
    """

    lookup = CountryLookup()
    tor_ips: set[str] = set()

    def __init__(self):
        super().__init__(daemon=True)
        self.start()

    def ip2country(self, ip: str):
        # Copy reference for thread-safe access.
        # This will probably never be required as the GIL will exist forever.
        local_tor_ips = self.tor_ips

        if ip in local_tor_ips:
            return 'XT'
            # XT code is available for custom purposes (https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#XT)

        return self.lookup.lookupStr(ip) or '--'

    def run(self):
        while True:
            try:
                self.refresh_tor_ips()
            except Exception:
                traceback.print_exc()
            time.sleep(6 * 60 * 60)     # 6h

    def refresh_tor_ips(self):
        r = requests.get('https://check.torproject.org/torbulkexitlist')
        r.raise_for_status()
        # Blindly trust that the format is correct:
        local_tor_ips = frozenset(r.text.strip().split('\n'))
        self.tor_ips = local_tor_ips
        print(f'Updated tor_ips with {len(local_tor_ips)} IPs')
