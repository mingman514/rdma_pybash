echo Start Tput Flow
taskset -c 1 ib_write_bw -l 64 -s 16 -q 8 --run_infinitely > /dev/null &
