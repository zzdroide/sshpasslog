# sshpasslog

Ever since I set up an SSH server exposed to the internet, I've been curious about what passwords are being attempted by the bots.

There are multiple programs that do this, but I didn't like how they logged the login attempts. So I searched for a Python implementation to modify it, and found some but I didn't like how they handled threading in the TCP server. Or how they used Paramiko: including dead channel handling code (never reached because auth is never successful).

So I rolled up my own and added some features. It was fun 😄

## Features

- Records some statistics about user/pass combinations, instead of just the combinations, or absolutely all the attempts (right now my DB has 400K rows, but `SUM(count)` is 9M)
- Records the country from which the login was attempted (or "XT" if it came from Tor)
- Records public key attempts too, and finds out if they match a public key in Github
- Logs all client attempts in real time
- Masks ssh version as a default non-hardened (`DebianBanner=yes`) up-to-date Ubuntu

// TODO: asciinema

### DB queries and examples

<!--
These tables are generated with:
sqlite3 -markdown sshpasslog.sqlite3 "SELECT * FROM pass ORDER BY count DESC LIMIT 5;"
-->

- The most attempted combos:
  ```sql
  SELECT *
  FROM pass
  ORDER BY count DESC;
  ```
  | user |   pass   | count |      first_at       |       last_at       |   last_ip    | last_country |
  |------|----------|-------|---------------------|---------------------|--------------|--------------|
  | root |          | 26203 | 2023-07-16 18:08:17 | 2025-03-15 00:31:55 | 218.92.0.203 | CN           |
  | root | root     | 16995 | 2023-07-15 15:28:17 | 2025-03-14 23:49:56 | 218.92.0.176 | CN           |
  | root | 123456   | 14863 | 2023-07-15 15:28:30 | 2025-03-14 19:24:10 | 218.92.0.219 | CN           |
  | root | admin    | 14291 | 2023-07-15 16:34:23 | 2025-03-14 23:47:57 | 218.92.0.176 | CN           |
  | root | password | 13838 | 2023-07-15 15:30:19 | 2025-03-14 20:27:43 | 218.92.0.223 | CN           |

- The most attempted usernames:
  ```sql
  SELECT user, SUM(count)
  FROM pass
  GROUP BY user
  ORDER BY SUM(count) DESC;
  ```
  |  user  | SUM(count) |
  |--------|------------|
  | root   | 7124009    |
  | admin  | 161947     |
  | user   | 159370     |
  | ubuntu | 66959      |
  | test   | 40934      |

- Which countries send the most attempts:
  ```sql
  SELECT last_country, SUM(count)
  FROM pass
  GROUP BY last_country
  ORDER BY SUM(count) DESC;
  ```
  | last_country | SUM(count) |
  |--------------|------------|
  | CN           | 6174823    |
  | US           | 740701     |
  | RU           | 543415     |
  | FR           | 302791     |
  | BR           | 120140     |

- Search for the attempt of a specific password:
  ```sql
  SELECT *
  FROM pass
  WHERE pass = 'napoleon'
  ORDER BY count DESC;
  ```
  |   user   |   pass   | count |      first_at       |       last_at       |    last_ip     | last_country |
  |----------|----------|-------|---------------------|---------------------|----------------|--------------|
  | root     | napoleon | 130   | 2023-07-21 18:19:24 | 2025-03-14 02:53:14 | 218.92.0.176   | CN           |
  | napoleon | napoleon | 10    | 2023-09-23 21:50:41 | 2025-02-14 03:08:36 | 138.197.103.58 | US           |
  | admin    | napoleon | 5     | 2024-12-23 11:17:49 | 2025-03-08 04:27:50 | 92.255.85.37   | RU           |
  | user     | napoleon | 5     | 2025-01-12 06:42:50 | 2025-03-13 11:40:40 | 80.64.30.77    | RU           |

### Github users from pubkeys

Public keys that attempted to authenticate can be traced back to Github users with [whoami.filippo.io](https://whoami.filippo.io)

Count unconsulted pubkeys:
```sh
sqlite3 sshpasslog.sqlite3 "SELECT COUNT(*) FROM pubk WHERE github_user IS NULL;"
```

Request all unconsulted pubkeys:
```sh
# Before doing this, run the "Count" query above and decide if you want to make this many requests to whoami.filippo.io xd

sqlite3 sshpasslog.sqlite3 "UPDATE pubk SET github_user = '.' WHERE github_user IS NULL;"
docker compose exec sshpasslog python -m src.get_githubs
```

```sql
SELECT *
FROM pubk
WHERE github_name IS NOT NULL
ORDER BY count DESC;
```
|       pubk       |    github_user    |  github_name  | count |      first_at       |       last_at       | last_user |    last_ip     | last_country |
|------------------|-------------------|---------------|-------|---------------------|---------------------|-----------|----------------|--------------|
| AAAAB3Nz...I7DAz | chengdada925      | @chengdada925 | 213   | 2023-08-03 10:56:44 | 2023-10-05 08:53:18 | cirros    | 114.224.80.9   | CN           |
| AAAAB3Nz...0qw== | sadiqumar18       | @sadiqumar18  | 56    | 2023-12-15 20:44:06 | 2025-03-06 04:58:52 | root      | 139.19.117.131 | DE           |
| AAAAB3Nz...oRw== | NishithP2004      | Nishith P     | 40    | 2023-12-16 14:24:34 | 2025-03-06 07:52:50 | root      | 139.19.117.131 | DE           |
| AAAAB3Nz...hYqBL | AbsolutelyVicious | 愤怒的蛋蛋         | 37    | 2024-01-12 15:08:33 | 2025-03-07 06:48:01 | root      | 139.19.117.131 | DE           |
| AAAAB3Nz...qQQ== | JiaT75            | Jia Tan       | 21    | 2024-03-29 19:16:30 | 2024-09-02 05:50:24 | udatabase | 139.19.117.131 | DE           |

## Installing

- Docker and openssh-client are assumed to be installed
- Clone this repository
- `./init.sh`
- `docker compose up -d --build`

### Docker's default logging

If the server is exposed to the internet at a public IPv4, on a common port like 22 or 2222, it will log **a lot**.

Print logs disk usage:
```sh
$ sudo du -h $(docker inspect --format='{{.LogPath}}' $(docker compose ps -q))
2.8G	/var/lib/docker/containers/a0f4…12-json.log
```
Manually clear logs:
```sh
docker compose up -d --force-recreate
```
To prevent any container from filling your disk with logs again, change the unbounded defaults. See the example [here](https://docs.docker.com/engine/logging/drivers/json-file/#usage) and don't miss this line: _Restart Docker for the changes to take effect for newly created containers. Existing containers don't use the new logging configuration automatically._

## Developing

- Python3.11 and Poetry are assumed to be installed
- Clone this repository
- `./init.sh`
- `poetry env use python3.11`
- `poetry install`
- ~~`poetry shell`~~ `eval $(poetry env activate)`
- `DEV=1 python -m src.main`

There's no autoreload! Remember, the server has to be stopped with ctrl-c and run again for changes to take effect.

And test with:

```
ssh -p2222 -v \
  -o IdentitiesOnly=yes \
  -o UserKnownHostsFile=/dev/null \
  -o StrictHostKeyChecking=<yes/no/ask> \
  -o PubkeyAuthentication=<yes/no> \
  user1@localhost
```

## Caveats

- Handles IPv4 only

- SQLite access should occur locally and [not over network](https://sqlite.org/useovernet.html)
  - Running queries directly on the server is OK
  - Running queries on a DB mounted over a network filesystem is _not_ OK. Work on a local copy of the DB instead.
