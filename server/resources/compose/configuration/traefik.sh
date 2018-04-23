#!/bin/sh
set -e

sed -i "s/DOMAIN/$DOMAIN/" ./configuration/traefik.toml
