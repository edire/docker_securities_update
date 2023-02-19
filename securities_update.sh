#!/bin/bash

docker run -d \
    # --platform linux/amd64 \
    -v "/home/ubuntu/volumes/securities_update":/volume \
    --env-file "/home/ubuntu/envs/securities_update.env" \
    edire/securities_update



# docker run -d -v "/home/ubuntu/volumes/securities_update":/volume --env-file "/home/ubuntu/envs/securities_update.env" edire/securities_update
# docker run -d -v "G:\My Drive\11 - Tech\docker_securities_update\volume":/volume --env-file "G:\My Drive\11 - Tech\docker_securities_update\.env" edire/securities_update

# linux/amd64
# linux/arm64
# linux/arm64/v8

# docker build -t edire/securities_update:0.0.2 -t edire/securities_update:latest --platform linux/arm64/v8 .
