#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-27 16:30:47

#script to get acceptance rate for each temperature and number of cells of accepted polymers
#Usage: bash optimum.sh <Nbar> <dphi>


mkdir dphi"$2"
mkdir dphi"$2"/Nbar"$1"
cp config_umbrella.py ./dphi"$2"/Nbar"$1"/config_umbrella.py
cp -r ConfGen.py ./dphi"$2"/Nbar"$1"/ConfGen.py
cp ~/soma_mod/install/bin/SOMA ./dphi"$2"/Nbar"$1"/SOMA
cp coord.xml ./dphi"$2"/Nbar"$1"/coord.xml
cd dphi"$2"/Nbar"$1"

rm *.csv


#calculate number of polymers
V=25
n=$((V*$1/2))
sed -i''  -e "s/NUM_POLY/$n/g" coord.xml
##create configuration
python3 ConfGen.py -i coord.xml
python3 config_umbrella.py coord.h5 $2 1
#run soma
./SOMA -c coord.h5 -a coord_ana.h5 -t 2 -r 0 > temp.csv
#grep data
grep 'T:' temp.csv | sed 's/^.*: //' > T.csv
grep 'Accrate:' temp.csv | sed 's/^.*: //' > acc_rate.csv
grep 'Best value:' temp.csv | sed 's/^.*: //' > opt.csv
grep 'Average num cells:' temp.csv | sed 's/^.*: //' > num_cells.csv
grep 'Maximum num monos:' temp.csv | sed 's/^.*: //' > max_monos_cell.csv
grep 'Initital polytypes:' temp.csv | sed 's/^.*: //' > initital_polytypes.csv
grep 'Flip attempts::' temp.csv | sed 's/^.*: //' > flips.csv
#grep 'Delta cost:' temp.csv | sed 's/^.*: //' > delta_cost.csv

# grep 'Polytypes before SA:' temp.csv | sed 's/^.*: //' > poly_types_before.csv
# grep 'Polytypes after SA:' temp.csv | sed 's/^.*: //' > poly_types_after.csv


#iterate over different seeds
for j in {1..49}
do
    echo "Seed: $j"
    #run soma
    ./SOMA -c coord.h5 -a coord_ana.h5 -t 2  -r $j > temp.csv
    #grep data
    grep 'Accrate:' temp.csv | sed 's/^.*: //' >> acc_rate.csv
    grep 'Best value:' temp.csv | sed 's/^.*: //' >> opt.csv
    grep 'Polytype before SA:' temp.csv | sed 's/^.*: //' >> poly_types_before.csv
    grep 'Polytype after SA:' temp.csv | sed 's/^.*: //' >> poly_types_after.csv
    grep 'Flip attempts::' temp.csv | sed 's/^.*: //' > flips.csv
    rm temp.csv
done




