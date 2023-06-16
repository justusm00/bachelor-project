#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-06-15 15:05:09

#script to get acceptance rate for each temperature and number of cells of accepted polymers
#Usage: bash optimum.sh <dphi> <total_density> <alpha> <Tmax>

mkdir alpha"$3"
mkdir alpha"$3"/dphi"$1"
cp config_umbrella.py ./alpha"$3"/dphi"$1"/config_umbrella.py
cp -r ConfGen.py ./alpha"$3"/dphi"$1"/ConfGen.py
cp ~/soma_mod/install/bin/SOMA ./alpha"$3"/dphi"$1"/SOMA
cp coord.xml ./alpha"$3"/dphi"$1"/coord.xml
cd alpha"$3"/dphi"$1"

rm *.csv


##create configuration
python3 ConfGen.py -i coord.xml
#get optimum with SD
python3 config_umbrella.py coord.h5 $1 $2 $3 -1.0
#run soma
./SOMA -c coord.h5 -t 1 -r 0 > temp.csv
grep 'MSE after flips at T=0:' temp.csv | sed 's/^.*: //' > opt_sd.csv
rm temp.csv

#optimum with SA
python3 config_umbrella.py coord.h5 $1 $2 $3 $4
#run soma
./SOMA -c coord.h5 -t 1 -r 0 > temp.csv
#grep data
grep 'T:' temp.csv | sed 's/^.*: //' > T.csv
grep 'Accrate:' temp.csv | sed 's/^.*: //' > acc_rate.csv
grep 'Flip attempts::' temp.csv | sed 's/^.*: //' > flips.csv
grep 'Best value:' temp.csv | sed 's/^.*: //' > opt.csv
grep 'Delta loss:' temp.csv | sed 's/^.*: //' > delta_loss.csv
rm temp.csv






