#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-08 10:47:27

#Usage: bash optimum_no_sa.sh <Nbar> 


mkdir Nbar"$1"_no_sa
cp config_umbrella.py ./Nbar"$1"_no_sa/config_umbrella.py
cp -r ConfGen.py ./Nbar"$1"_no_sa/ConfGen.py
cp -r SOMA ./Nbar"$1"_no_sa/SOMA
cd Nbar"$1"_no_sa

rm *.csv

cp ../coord_no_sa.xml ./coord.xml
#calculate number of polymers
V=25
n=$((V*$i/2))
sed -i''  -e "s/NUM_POLY/$n/g" coord.xml
echo "$i" >> Nbar.csv
##create configuration
python3 ConfGen.py -i coord.xml
python3 config_umbrella.py coord.h5 $1



