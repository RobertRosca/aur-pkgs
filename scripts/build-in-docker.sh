#!/bin/bash

set -euox pipefail

cp -r /src /tmp/src

chown -R nobody:nobody /tmp/src

cd /tmp/src || exit 1

HOME=/tmp/nobody runuser -p -unobody makepkg
