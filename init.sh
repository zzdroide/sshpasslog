#!/bin/sh
set -eu
cd "$(dirname "$0")"

echo "HOST_UID=$(id -u)" >.env
echo "HOST_GID=$(id -g)" >>.env

mkdir -p host_keys/etc/ssh/
ssh-keygen -A -f host_keys
