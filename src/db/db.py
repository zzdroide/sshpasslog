"""
DB is optimized for quick inserts and simplicity.

- No indices
- Not optimized for size (text timestamps, text IPs)
- This program only INSERTs.
"""

import sqlite3
import traceback

CREATEDB_QUERY = """
CREATE TABLE IF NOT EXISTS sshpasslog (
    user TEXT NOT NULL,
    pass TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    first_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_ip TEXT NOT NULL,
    last_country TEXT NOT NULL,
    PRIMARY KEY (user, pass)
);"""

INSERT_QUERY = """
INSERT INTO sshpasslog (user, pass, last_ip, last_country) VALUES (?, ?, ?, ?)
ON CONFLICT (user, pass) DO UPDATE SET
    count = count + 1,
    last_at = CURRENT_TIMESTAMP,
    last_ip = excluded.last_ip,
    last_country = excluded.last_country;
"""

con = sqlite3.connect(
    "./db/sshpassslog.sqlite3",
    check_same_thread=False,
    # autocommit=True,      future, python3.12
    isolation_level=None,
)

con.execute(CREATEDB_QUERY)


def record_pass(user: str, password: str, ip: str, country: str):
    try:
        con.execute(INSERT_QUERY, (user, password, ip, country))
    except (
        sqlite3.DataError,
        sqlite3.OperationalError,
        sqlite3.IntegrityError,
        sqlite3.InternalError,
    ):
        traceback.print_exc()
