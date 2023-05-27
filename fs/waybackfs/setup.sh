#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

source /tests/test_env.sh

mkdir -p /source
mkdir -p $DESTINATION
wayback -- /source $DESTINATION
