#!/bin/bash
# @Author: Your name
# @Date:   2023-02-08 12:10:47
# @Last Modified by:   Your name
# @Last Modified time: 2023-03-10 16:07:40

rm poly_time.csv
rm poly_opt.csv
rm poly_num.csv
##iterate over number of polymers
for (( i=5000; i<=20000; i+=2500 ))
do
    #change number of polymers in coord.xml
    sed -i'' -e "/<poly_arch>/,/<\/poly_arch>/ s/^.*A{32}/$i A{32}/g" coord.xml
    sed -i'' -e "/<poly_ar\ch>/,/<\/poly_ar\ch>/ s/^.*B{32}/$i B{32}/g" coord.xml

    #run simulation for different configurations
    for j in {1..100}
    do
        python3 ConfGen.py -i coord.xml
        wait
        python3 config_umbrella.py
        wait
        ./SOMA -c coord.h5 -t 1 > temp.txt
        grep 'Time spent :' temp.txt | sed 's/^.*: //' >> poly_time.csv
        grep 'MSE after flips at T=0:' temp.txt | sed 's/^.*: //' >> poly_opt.csv
        grep 'Flippable polymers:' temp.txt | sed 's/^.*: //' >> poly_num.csv
        rm temp.txt
        wait
    done
done