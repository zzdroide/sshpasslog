import threading
import time
import traceback

from ip3country import CountryLookup    # type: ignore
import requests


class Country(threading.Thread):

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
        self.tor_ips = frozenset(r.text.strip().split('\n'))
        # This is the only method that writes to self.tor_ips,
        # so reads should be thread-safe.
        print(f'Updated tor_ips with {len(self.tor_ips)} IPs')


country = Country() # Singleton

def ip2country(ip: str):
    return country.ip2country(ip)
