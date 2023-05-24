#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-15 14:55:19

#Usage: bash optimum_sa.sh <Nbar> 


mkdir Nbar$1
cp config_umbrella.py ./Nbar$1/config_umbrella.py
cp -r ConfGen.py ./Nbar$1/ConfGen.py
cp -r SOMA ./Nbar$1/SOMA
cd Nbar$1

rm *.csv
# Calculate the increment value for each step
for (( i=0; i<=4; i+=1 ))
do
    cp ../coord.xml ./coord.xml
    #calculate number of polymers
    V=25
    n=$((V*$1/2))
    alpha=$(bc <<< "scale=2; 0.5+$i/10")
    sed -i''  -e "s/NUM_POLY/$n/g" coord.xml
    echo "$alpha" >> alpha.csv
    ##create configuration
    python3 ConfGen.py -i coord.xml
    python3 config_umbrella.py coord.h5 0 $alpha
    wait
    #iterate over different seeds
    for j in {1..100}
    do
        echo "Alpha: $alpha, seed: $j"
        ./SOMA -c coord.h5 -t 1 -r $j> temp.txt
        grep 'MSE after flips at T=0:' temp.txt | sed 's/^.*: //' >> opt.csv
        grep 'Flip attempts:' temp.txt | sed 's/^.*: //' >> flips.csv
        grep 'Flippable polymers:' temp.txt | sed 's/^.*: //' >> flippable_polymers.csv
        rm temp.txt
    done
done
