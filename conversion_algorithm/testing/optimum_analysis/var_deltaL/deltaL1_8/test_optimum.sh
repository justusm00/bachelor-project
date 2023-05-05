#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-04 16:41:40

rm *.csv
##create configuration
python3 ConfGen.py -i coord.xml
wait
##iterate over discretizations
array=( 1 2 4 5 8 10 20 40)
#array=( 40)
for lam in "${array[@]}"
do
    echo "$lam" >> lam.csv
    python3 config_umbrella.py coord.h5 $lam
    wait
    #iterate over different seeds
    for i in {1..100}
    do
        ./SOMA -c coord.h5 -t 1 -r $i > temp.txt
        grep 'MSE after flips at T=0:' temp.txt | sed 's/^.*: //' >> opt.csv
        grep 'Flip attempts:' temp.txt | sed 's/^.*: //' >> flips.csv
        rm temp.txt
    done
done