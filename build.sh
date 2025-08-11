#!/bin/bash

# Exit if the script wasn't run from the project's root dir.
script_path="$(realpath "$0")"
script_dir="$(dirname "$script_path")"
if [ "$script_dir" != "$(pwd)" ]; then
    echo "build.sh must be run from BounceRL's root directory."
    exit 1
fi

# Clean up build directories
rm -rf build meson_build cython_build

# Build c/c++ libs
meson setup meson_build
cd meson_build
meson compile
cd ..

# Copy cffi and cython shared libs into the python module.
# Store libtime_control.so under /bounce_rl/libs
cd meson_build
rm -rf ../bounce_rl/libs
mkdir ../bounce_rl/libs
find . -name "*.so" | xargs -I '{}' cp --parents {} ../
cd ..

# Build python package
for PYTHON_VERSION in 39 310 311; do
    poetry env use "/opt/python/cp${PYTHON_VERSION}-cp${PYTHON_VERSION}/bin/python"
    poetry build
done

