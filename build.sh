#!/bin/bash

# Build c/c++ libs
meson setup meson_build
cd meson_build
meson compile
cd ..

# Copy the c/c++ libraries into the python package
cd meson_build
mkdir ../bounce_rl/libs
find . -name "*.so" | xargs -I '{}' cp --parents {} ../bounce_rl/libs
cd ..

# Build python package
poetry build
