Initialize with `./quickstart.sh`

Run with: `DEV=1 python -m src.main`

Remember that there's no autoreload, the server has to be stopped with ctrl-c and run again for changes to take effect.

And test with:

ssh -p2222 -v -o IdentitiesOnly=yes -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=`yes/no/ask` -o PubkeyAuthentication=`yes/no` user1@localhost


designed for ipv4 only

## DB queries

Country stats:
```sql
SELECT last_country, SUM(count) FROM pass GROUP BY last_country ORDER BY SUM(count) DESC;
```

Usernames:
```sql
SELECT user, SUM(count) FROM pass GROUP BY user;
```

## Github users from pubkeys

Count unconsulted:
```sh
sqlite3 db/sshpassslog.sqlite3 "SELECT COUNT(*) FROM pubk WHERE github_user IS NULL;"
```

Consult all unconsulted:
```sh
sqlite3 db/sshpassslog.sqlite3 "UPDATE pubk SET github_user = '.' WHERE github_user IS NULL;"
docker compose exec app python -m src.get_githubs
```
