#!/bin/bash -x

SCRIPT_DIR=$(dirname $0)

# Build the support bundle image
docker build -f Dockerfile -t support_bundle:1.1 .