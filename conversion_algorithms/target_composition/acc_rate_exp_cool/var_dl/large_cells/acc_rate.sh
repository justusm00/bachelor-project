#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-09 11:35:32

#Usage: bash optimum.sh <Nbar> 


rm *.csv


##create configuration
python3 ConfGen.py -i coord.xml
python3 config_umbrella.py coord.h5
#run soma
./SOMA -c coord.h5 -t 1 -r 0 > temp.csv
#grep data
grep 'T:' temp.csv | sed 's/^.*: //' > T.csv
grep 'Accrate:' temp.csv | sed 's/^.*: //' > acc_rate.csv
rm temp.csv
#iterate over different seeds
for j in {1..100}
do
    #run soma
    ./SOMA -c coord.h5 -t 1 -r $j > temp.csv
    #grep data
    grep 'Accrate:' temp.csv | sed 's/^.*: //' >> acc_rate.csv
    rm temp.csv
done




