Initialize with `./quickstart.sh`

Run with: `DEV=1 python -m src.main`

Remember that there's no autoreload, the server has to be stopped with ctrl-c and run again for changes to take effect.

And test with:

ssh -p2222 -v -o IdentitiesOnly=yes -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=`yes/no/ask` -o PubkeyAuthentication=`yes/no` nouser1@localhost


designed for ipv4 only

To obtain github users from pubkeys, in each interesting row set github_user to `.` , and run `python -m src.get_githubs`
