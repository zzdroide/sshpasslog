# No "import logging". This program is simple enough to just write to stdout.

ip_max_len = len('xxx.xxx.xxx.xxx')

class LoggingMixin:
    """Note: class should have `self.client_ip`."""
    def log(self, event: str, data=''):
        print(f'{self.client_ip.rjust(ip_max_len)}  {event: <4}  {data}')
