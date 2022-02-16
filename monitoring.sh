#!/bin/bash

while true
do 
    ps axo pcpu,comm | grep python | awk '{$1=$1};1' | cut -d ' ' -f 1 | paste -s -d+ - | bc >> cpu_usage

    sleep 1
done

# gnuplot -p -e "set yrange [0:1000]; set xrange [0:1200]; plot 'cpu_usage' with filledcurves above"
# cat cpu_usage | paste -s -d+ - | bc
