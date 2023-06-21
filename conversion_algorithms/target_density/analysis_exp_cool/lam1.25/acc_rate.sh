#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-06-20 20:00:50

#script to get acceptance rate for each temperature and number of cells of accepted polymers
#Usage: bash acc_rate.sh <dphi> <total_density> <alpha> <Tmax> <seed> 

mkdir alpha"$3"
mkdir alpha"$3"/dphi"$1"
mkdir alpha"$3"/dphi"$1"/seed"$5"
cp config_umbrella.py ./alpha"$3"/dphi"$1"/seed"$5"/config_umbrella.py
cp -r ConfGen.py ./alpha"$3"/dphi"$1"/seed"$5"/ConfGen.py
cp ~/soma_mod/install/bin/SOMA ./alpha"$3"/dphi"$1"/seed"$5"/SOMA
cp coord.xml ./alpha"$3"/dphi"$1"/seed"$5"/coord.xml
cd alpha"$3"/dphi"$1"/seed"$5"

rm *.csv


##create configuration
python3 ConfGen.py -i coord.xml
#get optimum with SD
python3 config_umbrella.py coord.h5 $1 $2 $3 -1.0
#run soma without anafile just to get loss function data
./SOMA -c coord.h5 -t 1 -r $5 > temp.csv
#grep data
grep 'MSE after flips at T=0:' temp.csv | sed 's/^.*: //' > opt_sd.csv
#run SOMA with anafile to get density field
#./SOMA -c coord.h5 -a coord_ana.h5 -t 2 -r $5 > temp.csv
rm temp.csv

#optimum with SA
python3 config_umbrella.py coord.h5 $1 $2 $3 $4
#run soma without anafile just to get loss function data
./SOMA -c coord.h5 -t 1 -r $5 > temp.csv
#grep data
grep 'T:' temp.csv | sed 's/^.*: //' > T.csv
grep 'Accrate:' temp.csv | sed 's/^.*: //' > acc_rate.csv
grep 'Flip attempts::' temp.csv | sed 's/^.*: //' > flips.csv
grep 'Best value:' temp.csv | sed 's/^.*: //' > opt.csv
grep 'MSE after flips at T=0:' temp.csv | sed 's/^.*: //' >> opt.csv
grep 'Delta loss:' temp.csv | sed 's/^.*: //' > delta_loss.csv
#run SOMA with anafile to get density field
#./SOMA -c coord.h5 -a coord_ana.h5 -t 2 -r $5 > temp.csv

rm temp.csv






