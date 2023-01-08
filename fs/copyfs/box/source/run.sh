#!/bin/bash

set -euo pipefail

ROOT_DIR=/tmp/copyfs
VERSION_DIR="$ROOT_DIR/versions"
FILES_DIR="$ROOT_DIR/files"

echo "ROOT_DIR: $ROOT_DIR"
echo "VERSION_DIR: $VERSION_DIR"
echo "FILES_DIR: $FILES_DIR"

umount $FILES_DIR || true
rm -rfv $ROOT_DIR
mkdir -pv $VERSION_DIR
mkdir -pv $FILES_DIR

echo "1:0:0755:0:0:files" > $VERSION_DIR/metadata.
chmod 700 $VERSION_DIR/metadata.
RCS_VERSION_PATH=$VERSION_DIR ./copyfs-daemon -f -d -s $FILES_DIR -o nonempty
