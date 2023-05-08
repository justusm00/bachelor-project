#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-07 18:12:13

#Usage: bash optimum_no_sa.sh <delta_phi> <lamella_width>


mkdir dphi"$1"_no_sa
cp config_umbrella.py ./dphi"$1"_no_sa/config_umbrella.py
cp -r ConfGen.py ./dphi"$1"_no_sa/ConfGen.py
cp -r SOMA ./dphi"$1"_no_sa/SOMA
cp coord_no_sa.xml ./dphi"$1"_no_sa/coord.xml
cd dphi"$1"_no_sa
##create configuration
python3 ConfGen.py -i coord.xml
rm *.csv
array=( 1 2 4 5 8 10 20 40)
# iterate over lamella widths
for lam in "${array[@]}"
do
    echo "$lam" >> lam.csv
    python3 config_umbrella.py coord.h5 $1 $lam
    #iterate over different seeds
    for j in {1..100}
    do
        echo "lam_width: $i, seed: $j"
        ./SOMA -c coord.h5 -t 1 -r $j> temp.txt
        grep 'MSE after flips at T=0:' temp.txt | sed 's/^.*: //' >> opt.csv
        grep 'Flip attempts:' temp.txt | sed 's/^.*: //' >> flips.csv
        grep 'Flippable polymers:' temp.txt | sed 's/^.*: //' >> flippable_polymers.csv
        rm temp.txt
    done
done
