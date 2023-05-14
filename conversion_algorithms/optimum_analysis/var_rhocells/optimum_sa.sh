#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-09 17:59:54

#Usage: bash optimum_sa.sh <delta_phi> 


mkdir dphi"$1"_sa
cp config_umbrella.py ./dphi"$1"_sa/config_umbrella.py
cp -r ConfGen.py ./dphi"$1"_sa/ConfGen.py
cp -r SOMA ./dphi"$1"_sa/SOMA
cd dphi"$1"_sa

rm *.csv
# Calculate the increment value for each step
for (( i=100; i<=300; i+=100 ))
do
    cp ../coord_sa.xml ./coord.xml
    #calculate number of polymers
    V=25
    n=$((V*$i/2))
    sed -i''  -e "s/NUM_POLY/$n/g" coord.xml
    echo "$i" >> Nbar.csv
    ##create configuration
    python3 ConfGen.py -i coord.xml
    python3 config_umbrella.py coord.h5 $1
    wait
    #iterate over different seeds
    for j in {1..100}
    do
        echo "Nbar: $i, seed: $j"
        ./SOMA -c coord.h5 -t 1 -r $j> temp.txt
        grep 'MSE after flips at T=0:' temp.txt | sed 's/^.*: //' >> opt.csv
        grep 'Flip attempts:' temp.txt | sed 's/^.*: //' >> flips.csv
        grep 'Flippable polymers:' temp.txt | sed 's/^.*: //' >> flippable_polymers.csv
        rm temp.txt
    done
done
