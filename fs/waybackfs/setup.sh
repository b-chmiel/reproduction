#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

source test_template_env.sh

mkdir -p /source
mkdir -p $DESTINATION
wayback -- /source $DESTINATION
