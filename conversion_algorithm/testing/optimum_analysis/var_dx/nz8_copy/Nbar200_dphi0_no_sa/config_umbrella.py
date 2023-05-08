# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2023-01-25 16:59:12
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-06 19:08:08
import h5py
import numpy as np
import sys

coordfile=sys.argv[1] ##file to be modified
delta_phi=float(sys.argv[2]) ##delta phi
##file that contains area51 and bead positions


f= h5py.File(coordfile, 'r+') 
e = "umbrella_field" in f
if e:
    del f["umbrella_field"]
e= "area51" in f
if e:
    del f["area51"]


lamella_width = 1##width of umbrella field lamella in cell
n=lamella_width
offset=1 ##to account for area51 (and maybe density drop next to it)




nxyz=np.array(f['parameter/nxyz'])
umb_field=np.zeros((2,nxyz[0],nxyz[1],nxyz[2]))
##fill umbrella field with negative values
umb_field.fill(-1)


##define target values
vals=np.array([0.5-delta_phi,0.5+delta_phi])

m=int((nxyz[0]-2*offset)/n)
# Use nested for loops to assign the checkerboard-like values
for i in range(m):
    for j in range(m):
        if (i+j) % 2 == 0:  
            umb_field[0,offset+i*n:offset+(i+1)*n, offset, offset + j*n:offset +(j+1)*n] = vals[0]
            umb_field[1,offset+i*n:offset+(i+1)*n, offset, offset + j*n:offset +(j+1)*n] = vals[1]
        else:
            umb_field[1,offset+i*n:offset+(i+1)*n, offset, offset + j*n:offset +(j+1)*n] = vals[0]
            umb_field[0,offset+i*n:offset+(i+1)*n, offset, offset + j*n:offset +(j+1)*n] = vals[1]






##add umbrella field to f
dset_umb = f.create_dataset("umbrella_field", data=umb_field)
f.close()