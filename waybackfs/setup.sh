#!/bin/bash

set -euo pipefail

source test_template_env.sh

mkdir -p /source
mkdir -p $DESTINATION
wayback -- /source $DESTINATION
