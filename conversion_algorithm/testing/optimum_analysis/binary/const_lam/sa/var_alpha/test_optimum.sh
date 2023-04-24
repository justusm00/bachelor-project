#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-04-23 22:08:04

#remove old files
rm *.csv

#iterate over temperatures
for i in {1..10}
do
    t=$(echo "scale=5; 0.8+$i/100" | bc -l)
    echo "$t" >> alpha.csv
    sed -i''  -e "s/<alpha>.*/<alpha>$t<\/alpha>/g" coord.xml
    #modify coord.xml Tmax
    
    ##create configuration
    python3 ConfGen.py -i coord.xml
    wait
    python3 config_umbrella.py coord.h5 1
    wait
    #iterate over different seeds
    for j in {1..1000}
    do
        ./SOMA -c coord.h5 -t 1  > temp.txt
        grep 'MSE after flips at T=0:' temp.txt | sed 's/^.*: //' >> opt.csv
        rm temp.txt
        #wait one second to obtain new seed
        sleep 0.5
    done
done