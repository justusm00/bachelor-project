#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-06-27 14:21:16

#script to get acceptance rate for each temperature and number of cells of accepted polymers
#Usage: bash opt.sh 

rm *.csv
##create configuration
python3 ConfGen.py -i coord.xml
python3 config_umbrella.py coord.h5 0.5 0 1.0
#run soma
./SOMA -c coord.h5 -a coord_ana.h5 -t 1000 -r 0 > temp.csv
grep 'MSE after flips at T=0:' temp.csv | sed 's/^.*: //' > opt.csv





