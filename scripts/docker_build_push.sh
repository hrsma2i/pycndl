#!/bin/sh -eu
SCRIPTS_DIR=$(
    cd "$(dirname "$0")"
    pwd
)
PRJ_ROOT=$(dirname "$SCRIPTS_DIR")

IMAGE=ghcr.io/hrsma2i/pycndl

if [ "$(git status --porcelain)" ]; then
    TAG='test'
else
    TAG=gitsha-$(git rev-parse HEAD)
fi

echo "tag: $TAG"
docker build -t "$IMAGE:$TAG" "$PRJ_ROOT"
docker push "$IMAGE:$TAG"

if [ ! "$(git status --porcelain)" ]; then
    docker tag "$IMAGE:$TAG" "$IMAGE:latest"
    docker push "$IMAGE:latest"
fi
