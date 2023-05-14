#!/bin/bash
# @Author: Your name
# @Date:   2023-02-08 12:10:47
# @Last Modified by:   Your name
# @Last Modified time: 2023-04-19 13:53:39

#script to run optimization algorithm for varying system size at constant sqrt(N_bar)=100

rm time.csv
rm opt.csv
rm length.csv
##iterate over x and z lengths
for (( i=2; i<=20; i+=1 ))
do
    #calculate number of polymers=100*lx^2
    let n=100*i*i
    #calculate number of gridpoints in x and z direction
    let nx=8*i
    #change number of polymers in coord.xml
    sed -i'' -e "/<poly_arch>/,/<\/poly_arch>/ s/^.*A{32}/$n A{32}/g" coord.xml
    sed -i'' -e "/<poly_arch>/,/<\/poly_arch>/ s/^.*B{32}/$n B{32}/g" coord.xml

    #change lengths and grid points
    sed -i''  -e "s/<lxyz>.*/<lxyz>$i 1 $i<\/lxyz>/g" coord.xml
    sed -i''  -e "s/<nxyz>.*/<nxyz>$nx 8 $nx<\/nxyz>/g" coord.xml

    #create configurations
    python3 ConfGen.py -i coord.xml
    wait
    python3 config_umbrella.py
    wait

    #run simulation for different configurations
    for j in {1..10}
    do

        ./SOMA -c coord.h5 -t 1 > temp.txt
        grep 'Flip attempts:' temp.txt | sed 's/^.*: //' >> time.csv
        grep 'MSE after flips at T=0:' temp.txt | sed 's/^.*: //' >> opt.csv
        echo "$i" >> length.csv
        rm temp.txt
        wait
    done
done