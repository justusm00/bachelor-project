#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-16 11:57:56

#script to extract number cells polymers have monomers in without optimization
#Usage: bash optimum.sh <Nbar> 


mkdir num_cells_Nbar"$1"
cp config_umbrella.py ./num_cells_Nbar"$1"/config_umbrella.py
cp -r ConfGen.py ./num_cells_Nbar"$1"/ConfGen.py
cp ~/soma_mod/install/bin/SOMA ./num_cells_Nbar"$1"/SOMA
cp coord.xml ./num_cells_Nbar"$1"/coord.xml
cd num_cells_Nbar"$1"

rm *.csv


#calculate number of polymers
V=25
n=$((V*$1/2))
sed -i''  -e "s/NUM_POLY/$n/g" coord.xml
##create configuration
python3 ConfGen.py -i coord.xml
python3 config_umbrella.py coord.h5 0
#run soma
./SOMA -c coord.h5 -t 1 -r 0 > temp.csv
#grep data
grep 'Num cells:' temp.csv | sed 's/^.*: //' > num_cells.csv

# #iterate over different seeds
# for j in {1..1}
# do
#     #run soma
#     ./SOMA -c coord.h5 -t 1 -r $j > temp.csv
#     #grep data
#     grep 'Accrate:' temp.csv | sed 's/^.*: //' >> acc_rate.csv
#     grep 'Best value:' temp.csv | sed 's/^.*: //' > opt.csv
#     rm temp.csv
# done




