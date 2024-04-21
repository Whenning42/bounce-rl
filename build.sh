#!/bin/bash

# Build c/c++ libs
cd bounce_rl
pwd
meson setup ../build
cd ../build
meson compile
mkdir lib
find . -name "*.so" ! -path "./lib/*" | xargs -I '{}' cp {} lib/;
cd ../bounce_rl

# Build python wheel
poetry build
