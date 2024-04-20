#!/bin/bash

cd bounce_rl
meson setup build/bounce_rl
cd build/bounce_rl
meson compile
