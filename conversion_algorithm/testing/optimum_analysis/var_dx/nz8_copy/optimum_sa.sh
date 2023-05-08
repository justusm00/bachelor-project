#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-06 14:44:50

#Usage: bash optimum_sa.sh <Nbar> <delta_phi> 


mkdir Nbar"$1"_dphi"$2"_sa
cp config_umbrella.py ./Nbar"$1"_dphi"$2"_sa/config_umbrella.py
cp coord_sa.xml ./Nbar"$1"_dphi"$2"_sa/coord.xml
cp -r ConfGen.py ./Nbar"$1"_dphi"$2"_sa/ConfGen.py
cp -r SOMA ./Nbar"$1"_dphi"$2"_sa/SOMA
cd Nbar"$1"_dphi"$2"_sa
#calculate number of polymers
V=100
n=$((V*$1/2))
sed -i''  -e "s/NUM_POLY/$n/g" coord.xml
rm *.csv
# Calculate the increment value for each step
for i in {1..10}
do
    dx=$(echo "scale=4; $i/10" | bc)
    nx=$(echo "scale=0; 10/$dx" | bc)
    echo "$dx" >> dx.csv
    sed -i''  -e "s/<nxyz>.*/<nxyz>$nx 8 $nx<\/nxyz>/g" coord.xml
    ##create configuration
    python3 ConfGen.py -i coord.xml
    python3 config_umbrella.py coord.h5 $2
    wait
    #iterate over different seeds
    for i in {1..100}
    do
        echo "dx: $dx, seed: $i"
        ./SOMA -c coord.h5 -t 1 -r $i > temp.txt
        grep 'MSE after flips at T=0:' temp.txt | sed 's/^.*: //' >> opt.csv
        grep 'Flip attempts:' temp.txt | sed 's/^.*: //' >> flips.csv
        rm temp.txt
    done
done
