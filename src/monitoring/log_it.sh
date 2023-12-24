#!/bin/bash
set -eu

while true; do
    printf "$(date +%H:%M:%S): "; eval $1
    sleep 1
done
