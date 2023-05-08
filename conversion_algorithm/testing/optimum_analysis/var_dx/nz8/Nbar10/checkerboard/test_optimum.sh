#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-05 18:12:07

rm *.csv

# Calculate the increment value for each step
for i in {1..20}
do
    dx=$(echo "scale=4; $i/20" | bc)
    nx=$(echo "scale=0; 10/$dx" | bc)
    echo "$dx" >> dx.csv
    sed -i''  -e "s/<nxyz>.*/<nxyz>$nx 1 $nx<\/nxyz>/g" coord.xml
    ##create configuration
    python3 ConfGen.py -i coord.xml
    python3 config_umbrella.py coord.h5 1
    wait
    #iterate over different seeds
    for i in {1..100}
    do
        ./SOMA -c coord.h5 -t 1 -r $i > temp.txt
        grep 'MSE after flips at T=0:' temp.txt | sed 's/^.*: //' >> opt.csv
        grep 'Flip attempts:' temp.txt | sed 's/^.*: //' >> flips.csv
        rm temp.txt
    done
done