#!/bin/sh -eu
SCRIPTS_DIR=$(
    cd "$(dirname "$0")"
    pwd
)
PRJ_ROOT=$(dirname "$SCRIPTS_DIR")

IMAGE_URI=ghcr.io/hrsma2i/pycndl

GIT_SHA=$(git rev-parse HEAD)
URI_TAG="$IMAGE_URI:gitsha-$GIT_SHA"

docker build -t "$URI_TAG" "$PRJ_ROOT"
docker push "$URI_TAG"
