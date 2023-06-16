#!/bin/bash
# @Author: Your name
# @Date:   2023-02-09 11:41:03
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-17 22:00:13

#script to get acceptance rate for each temperature and number of cells of accepted polymers
#Usage: bash optimum.sh <dphi>


rm *.csv

##create configuration
python3 ConfGen.py -i coord.xml
python3 config_umbrella.py coord.h5 $1 0
#run soma
./SOMA -c coord.h5 -a coord_ana.h5 -t 2 -r 0 


#iterate over different seeds
for j in {1..9}
do
    #run soma
    ./SOMA -c coord.h5 -a coord_ana.h5 -t 2  -r $j 
done




