#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-04-19 14:28:22

##iterate over lamella periodicity
for lam in {1..9} ##lamella width
do
    echo "$lam" >> lam.csv
    ##create configuration
    python3 ConfGen.py -i coord.xml
    wait
    python3 config_umbrella.py coord.h5 $lam
    wait
    #iterate over different seeds
    for i in {1..10}
    do
        ./SOMA -c coord.h5 -t 1 > temp.txt
        grep 'MSE after flips at T=0:' temp.txt | sed 's/^.*: //' >> opt.csv
        rm temp.txt
    done
done