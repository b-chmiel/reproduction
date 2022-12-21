#!/bin/bash

set -euo pipefail

rm -rfv /tmp/copyfs
mkdir -pv /tmp/copyfs/{files,versions}
echo "1:0:0755:0:0:$(basename /tmp/copyfs/files)" > /tmp/copyfs/files/metadata.
chmod 700 /tmp/copyfs/files/metadata.
RCS_VERSION_PATH=/tmp/copyfs/versions ./copyfs-daemon -f -d -s /tmp/copyfs/files -o nonempty
