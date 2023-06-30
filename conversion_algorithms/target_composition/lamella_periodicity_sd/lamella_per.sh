#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-06-30 15:12:31

#script to get acceptance rate for each temperature and number of cells of accepted polymers
#Usage: bash optimum.sh <lam>

mkdir lam"$1"
cp config_umbrella.py ./lam"$1"/config_umbrella.py
cp -r ConfGen.py ./lam"$1"/ConfGen.py
cp ~/soma_mod/install/bin/SOMA ./lam"$1"/SOMA
cp coord.xml ./lam"$1"/coord.xml
cd lam"$1"

rm *.csv


#calculate number of polymers
V=100
n=$((V*100/2))
sed -i''  -e "s/NUM_POLY/$n/g" coord.xml
##create configuration
python3 ConfGen.py -i coord.xml
python3 config_umbrella.py coord.h5 0.5 0 1.0 $1
#run soma
./SOMA -c coord.h5 -a coord_ana.h5 -t 2 -r 0 > temp.csv
grep 'MSE after flips at T=0:' temp.csv | sed 's/^.*: //' > opt.csv


#iterate over different seeds
for j in {1..49}
do
    echo "seed: $j"
    #run soma
    ./SOMA -c coord.h5 -a coord_ana.h5 -t 2  -r $j > temp.csv
    grep 'MSE after flips at T=0:' temp.csv | sed 's/^.*: //' >> opt.csv
done




