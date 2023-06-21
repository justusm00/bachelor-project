#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-06-17 17:36:24

#script to get acceptance rate for each temperature and number of cells of accepted polymers
#Usage: bash optimum.sh <lam> <dphi> <total_density> 


mkdir lam"$1"
mkdir lam"$1"/dphi"$2"
cp config_umbrella.py ./lam"$1"/dphi"$2"/config_umbrella.py
cp -r ConfGen.py ./lam"$1"/dphi"$2"/ConfGen.py
cp ~/soma_mod/install/bin/SOMA ./lam"$1"/dphi"$2"/SOMA
cp coord.xml ./lam"$1"/dphi"$2"/coord.xml
cd lam"$1"/dphi"$2"

rm *.csv


#calculate number of polymers
V=25
n=$((V*100/2))
sed -i''  -e "s/NUM_POLY/$n/g" coord.xml
##create configuration
python3 ConfGen.py -i coord.xml
python3 config_umbrella.py coord.h5 $1 $2 $3 10.0
#run soma
./SOMA -c coord.h5 -a coord_ana.h5 -t 2 -r 0  > temp.csv
grep 'MSE after flips at T=0:' temp.csv | sed 's/^.*: //' > opt.csv
rm temp.csv
#iterate over different seeds
for j in {1..49}
do
    echo "Seed: $j"
    #run soma
    ./SOMA -c coord.h5 -a coord_ana.h5 -t 2 -r $j  > temp.csv
    grep 'MSE after flips at T=0:' temp.csv | sed 's/^.*: //' > opt.csv
    rm temp.csv
done




