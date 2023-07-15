#!/bin/sh
echo "HOST_UID=$(id -u)" >.env
echo "HOST_GID=$(id -g)" >>.env
