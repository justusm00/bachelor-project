#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-15 22:35:32

#Usage: bash optimum.sh <Nbar> 


mkdir Nbar"$1"
cp config_umbrella.py ./Nbar"$1"/config_umbrella.py
cp -r ConfGen.py ./Nbar"$1"/ConfGen.py
cp ~/soma_mod/install/bin/SOMA ./Nbar"$1"/SOMA
cp coord.xml ./Nbar"$1"/coord.xml
cd Nbar"$1"

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
grep 'T:' temp.csv | sed 's/^.*: //' > T.csv
grep 'Accrate:' temp.csv | sed 's/^.*: //' > acc_rate.csv
grep 'Best value:' temp.csv | sed 's/^.*: //' > opt.csv

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




