import functools
import logging
import sys

stdout_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler("sshpasslog.log")
file_handler.setFormatter(
    logging.Formatter(fmt="%(asctime)s  %(message)s", datefmt="%Y-%m-%d %H:%M"),
)

status_logger = logging.getLogger()
status_logger.setLevel(logging.INFO)
status_logger.addHandler(stdout_handler)
status_logger.addHandler(file_handler)

access_logger = logging.getLogger("access_logger")
access_logger.setLevel(logging.INFO)
access_logger.addHandler(stdout_handler)
access_logger.propagate = False


ip_max_len = len("xxx.xxx.xxx.xxx")


class LoggingMixin:
    """Note: class should have `self.client_ip_addr` and `self.client_ip_country`."""

    client_ip_addr: str
    client_ip_country: str

    def log_access(self, event: str, data=""):
        ip_part = f"{self.client_ip_country} {self.client_ip_addr.rjust(ip_max_len)}"
        access_logger.info(f"{ip_part}  {event: <4}  {data}")


def log_exceptions():
    """Manually logs exceptions in this function, as Paramiko's logger is silenced."""
    def real_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                status_logger.exception("")
                raise

        return wrapper
    return real_decorator
