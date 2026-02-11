"""
DB is optimized for quick inserts and simplicity.

- No extra indices (other than primary keys)
- Not optimized for size (text timestamps, text IPs)
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
    github_user TEXT DEFAULT NULL,
    github_name TEXT DEFAULT NULL,
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

GET_PUBK_TO_OBTAIN_GITHUB = """
SELECT pubk FROM pubk WHERE github_user = '.';
"""

SET_GITHUB_TO_PUBK = """
UPDATE pubk SET github_user = ?, github_name = ? WHERE pubk = ?;
"""

con = sqlite3.connect(
    "./sshpasslog.sqlite3",
    check_same_thread=False,
    # autocommit=True,      Future, python3.12. But paramiko still supports up to 3.11 only
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


def github_pubkeys_to_obtain():
    tuples = con.execute(GET_PUBK_TO_OBTAIN_GITHUB).fetchall()
    return (t[0] for t in tuples)


def set_github_to_pubk(pubk: str, *, github_user: str, github_name: str | None):
    cur = con.execute(SET_GITHUB_TO_PUBK, (github_user, github_name, pubk))

    if cur.rowcount != 1:
        msg = f"Update to pubk modified {cur.rowcount} rows: {pubk}"
        raise RuntimeError(msg)
