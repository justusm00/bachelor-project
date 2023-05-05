#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-04-30 16:41:10

#remove old files
rm *.csv
##create configuration
python3 ConfGen.py -i coord.xml
wait
python3 config_umbrella.py coord.h5 1
wait
#iterate over different seeds
for i in {1..1000}
do
    ./SOMA -c coord.h5 -t 1 -r $i > temp.txt
    grep 'MSE after flips at T=0:' temp.txt | sed 's/^.*: //' >> opt.csv
    rm temp.txt
    #wait one second to obtain new seed
done
