#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-06-23 16:34:19

#script to get acceptance rate for each temperature and number of cells of accepted polymers
#Usage: bash lamella_per.sh <dphi> <total_density> 

mkdir dphi"$1"
cp config_umbrella.py ./dphi"$1"/config_umbrella.py
cp -r ConfGen.py ./dphi"$1"/ConfGen.py
cp ~/soma_mod/install/bin/SOMA ./dphi"$1"/SOMA
cp coord.xml ./dphi"$1"/coord.xml
cd dphi"$1"/

rm *.csv


#calculate number of polymers
V=125
n=$((V*100/2))
sed -i''  -e "s/NUM_POLY/$n/g" coord.xml
##create configuration
python3 ConfGen.py -i coord.xml
python3 config_umbrella.py coord.h5 $1 $2 0.999 -1 5
#run soma
./SOMA -c coord.h5 -a coord_ana.h5 -t 2 -r 0 > temp.csv
grep 'MSE after flips at T=0:' temp.csv | sed 's/^.*: //' > opt.csv


#iterate over different seeds
for j in {1..99}
do
    echo "seed: $j"
    #run soma
    ./SOMA -c coord.h5 -a coord_ana.h5 -t 2 -r $j > temp.csv
    grep 'MSE after flips at T=0:' temp.csv | sed 's/^.*: //' >> opt.csv
done




