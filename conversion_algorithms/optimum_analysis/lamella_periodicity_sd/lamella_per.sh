#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-24 15:43:40

#script to get acceptance rate for each temperature and number of cells of accepted polymers
#Usage: bash optimum.sh <Nbar> <lam>

mkdir lam"$2"
mkdir lam"$2"/Nbar"$1"
cp config_umbrella.py ./lam"$2"/Nbar"$1"/config_umbrella.py
cp -r ConfGen.py ./lam"$2"/Nbar"$1"/ConfGen.py
cp ~/soma_mod/install/bin/SOMA ./lam"$2"/Nbar"$1"/SOMA
cp coord.xml ./lam"$2"/Nbar"$1"/coord.xml
cd lam"$2"/Nbar"$1"

rm *.csv


#calculate number of polymers
V=25
n=$((V*$1/2))
sed -i''  -e "s/NUM_POLY/$n/g" coord.xml
##create configuration
python3 ConfGen.py -i coord.xml
python3 config_umbrella.py coord.h5 0.49 0 $2
#run soma
./SOMA -c coord.h5 -a coord_ana.h5 -t 2 -r 0 > temp.csv
grep 'MSE after flips at T=0:' temp.csv | sed 's/^.*: //' > opt.csv


#iterate over different seeds
for j in {1..49}
do
    #run soma
    ./SOMA -c coord.h5 -a coord_ana.h5 -t 2  -r $j > temp.csv
    grep 'MSE after flips at T=0:' temp.csv | sed 's/^.*: //' >> opt.csv
done




