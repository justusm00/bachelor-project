#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-22 10:10:19

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
python3 config_umbrella.py coord.h5 $2 0
#run soma
./SOMA -c coord.h5 -a coord_ana.h5 -t 2 -r 0 


#iterate over different seeds
for j in {1..49}
do
    #run soma
    ./SOMA -c coord.h5 -a coord_ana.h5 -t 2  -r $j 
done




