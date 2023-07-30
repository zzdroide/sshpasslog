"""
DB is optimized for quick inserts and simplicity.

- No indices
- Not optimized for size (text timestamps, text IPs)
- This program only INSERTs.
"""

import sqlite3
import traceback

CREATEDB_QUERIES = ("""
CREATE TABLE IF NOT EXISTS pass (
    user TEXT NOT NULL,
    pass TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    first_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_ip TEXT NOT NULL,
    last_country TEXT NOT NULL,
    PRIMARY KEY (user, pass)
);
""",
""" -- # noqa: E128
CREATE TABLE IF NOT EXISTS pubk (
    pubk TEXT PRIMARY KEY NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    first_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_user TEXT NOT NULL,
    last_ip TEXT NOT NULL,
    last_country TEXT NOT NULL
);
""")

INSERT_PASS_QUERY = """
INSERT INTO pass (user, pass, last_ip, last_country) VALUES (?, ?, ?, ?)
ON CONFLICT (user, pass) DO UPDATE SET
    count = count + 1,
    last_at = CURRENT_TIMESTAMP,
    last_ip = excluded.last_ip,
    last_country = excluded.last_country;
"""  # noqa: S105

INSERT_PUBK_QUERY = """
INSERT INTO pubk (pubk, last_user, last_ip, last_country) VALUES (?, ?, ?, ?)
ON CONFLICT (pubk) DO UPDATE SET
    count = count + 1,
    last_at = CURRENT_TIMESTAMP,
    last_user = excluded.last_user,
    last_ip = excluded.last_ip,
    last_country = excluded.last_country;
"""

con = sqlite3.connect(
    "./db/sshpassslog.sqlite3",
    check_same_thread=False,
    # autocommit=True,      future, python3.12
    isolation_level=None,
)

for query in CREATEDB_QUERIES:
    con.execute(query)


def execute_graceful(sql, parameters):
    try:
        con.execute(sql, parameters)
    except (
        sqlite3.DataError,
        sqlite3.OperationalError,
        sqlite3.IntegrityError,
        sqlite3.InternalError,
    ):
        traceback.print_exc()


def record_pass(user: str, password: str, ip: str, country: str):
    execute_graceful(INSERT_PASS_QUERY, (user, password, ip, country))


def record_pubk(user: str, pubk: str, ip: str, country: str):
    execute_graceful(INSERT_PUBK_QUERY, (pubk, user, ip, country))
