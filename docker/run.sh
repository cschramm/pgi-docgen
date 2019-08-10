#!/bin/bash

set -e

TAG="lazka/pgi-docgen"

sudo docker run --security-opt label=disable \
    --rm  --volume "$(pwd)/..:/home/user/app" \
    --tty --interactive "${TAG}" bash
