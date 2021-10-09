#!/bin/sh -eu
SCRIPTS_DIR=$(
    cd "$(dirname "$0")"
    pwd
)
PRJ_ROOT=$(dirname "$SCRIPTS_DIR")

IMAGE_URI=ghcr.io/hrsma2i/pycndl

docker build -t $IMAGE_URI "$PRJ_ROOT"
docker push $IMAGE_URI
