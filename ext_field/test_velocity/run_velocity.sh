#!/bin/bash
# @Author: Your name
# @Date:   2023-02-28 11:43:50
# @Last Modified by:   Your name
# @Last Modified time: 2023-02-28 11:50:35


##first run
mpiexec -n 1 ./SOMA -c coord.h5 -a coord_ana.h5  -t 100 -o 0
for time in {1..100}
do
    ##move external field one grid point in y direction
    python3 move_field.py
    ##run SOMA with end.h5
    mpiexec -n 1 ./SOMA -c end.h5 -a coord_ana.h5  -t 100 -o 0
done