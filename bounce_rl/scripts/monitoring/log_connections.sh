#!/bin/bash

trap "kill $(jobs -p)" EXIT
./log_it.sh 'xrestop -b -m 1' > xres_out.txt &
./log_it.sh 'ps -A -o pid,ppid,comm,command' > pid_out.txt &
wait
