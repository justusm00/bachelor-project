#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-02-09 13:51:01

##iterate over lamella periodicity
for lam in {1..9} ##lamella width
do
    rm opt_$lam.txt
    ##iterate over configurations
    for i in {1..9}
    do
        python3 config_umbrella.py coord_$i.h5 $lam
        wait
        ##repeat with different seeds
        for j in {1..10}
        do
            ./SOMA -c coord_$i.h5 -t 1 | grep 'MSE final:' | sed 's/^.*: //' >> opt_$lam.txt
        done
        wait
    done
done