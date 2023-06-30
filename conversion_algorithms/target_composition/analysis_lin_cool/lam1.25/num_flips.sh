#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-27 16:49:45

#script to get acceptance rate for each temperature and number of cells of accepted polymers
#Usage: bash optimum.sh <dphi>


mkdir num_flips/dphi"$1"
mkdir num_flips/dphi"$1"
cp config_umbrella.py ./num_flips/dphi"$1"/config_umbrella.py
cp -r ConfGen.py ./num_flips/dphi"$1"/ConfGen.py
cp ~/soma_mod/install/bin/SOMA ./num_flips/dphi"$1"/SOMA
cp coord.xml ./num_flips/dphi"$1"/coord.xml
cd num_flips/dphi"$1"

rm *.csv


#calculate number of polymers
V=25
for i in {100..150}
do
    n=$((V*$i/2))
    sed -i''  -e "s/NUM_POLY/$n/g" coord.xml
    ##create configuration
    python3 ConfGen.py -i coord.xml
    python3 config_umbrella.py coord.h5 $1 1
    #run soma
    ./SOMA -c coord.h5 -a coord_ana.h5 -t 1 -r 0 > temp.csv
    grep 'Flip attempts:' temp.csv | sed 's/^.*: //' > flips.csv
    echo "$n" >> n_poly.csv
    #grep 'Delta cost:' temp.csv | sed 's/^.*: //' > delta_cost.csv

    # grep 'Polytypes before SA:' temp.csv | sed 's/^.*: //' > poly_types_before.csv
    # grep 'Polytypes after SA:' temp.csv | sed 's/^.*: //' > poly_types_after.csv


    #iterate over different seeds
    for j in {1..49}
    do
        echo "Seed: $j"
        #run soma
        ./SOMA -c coord.h5 -a coord_ana.h5 -t 1  -r $j > temp.csv
        grep 'Flip attempts:' temp.csv | sed 's/^.*: //' >> flips.csv
        rm temp.csv
    done
done




