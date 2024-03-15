#!/bin/sh
# Meson's install doesn't like renaming .so's, so we do it with a custom install script
# instead.

sudo cp core/time_control/libtime_control.so /usr/lib/libtime_control.so
sudo cp core/time_control/libtime_control32.so /usr/lib32/libtime_control.so