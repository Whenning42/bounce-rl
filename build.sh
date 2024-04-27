#!/bin/bash

# Build c/c++ libs
cd bounce_rl
pwd
meson setup ../build
cd ../build
meson compile
mkdir libs
find . -name "*.so" ! -path "./lib/*" | xargs -I '{}' cp {} libs;
cd ../bounce_rl
mv ../build/libs ./

# Build python wheel
poetry build

# Upload the wheel
twine upload --repository testpypi dist/*.whl
