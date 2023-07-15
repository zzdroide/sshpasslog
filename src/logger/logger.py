# No "import logging". This program is simple enough to just write to stdout.

ip_max_len = len('xxx.xxx.xxx.xxx')

class LoggingMixin:
    """Note: class should have `self.client_ip_addr` and `self.client_ip_country`."""

    client_ip_addr: str
    client_ip_country: str

    def log(self, event: str, data=''):
        ip_part = f'{self.client_ip_country} {self.client_ip_addr.rjust(ip_max_len)}'
        print(f'{ip_part}  {event: <4}  {data}')
