# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2023-01-25 16:59:12
# @Last Modified by:   Your name
# @Last Modified time: 2023-01-25 18:00:17
import h5py
import numpy as np

##file that contains area51 and bead positions
f= h5py.File('coord_sample_t50000.h5', 'r+') 
##file that contains polyconverison info
g=h5py.File('coord_umb.h5', 'r+')
nxyz=np.array(f['parameter/nxyz'])
offset=3 ##to account for density drop close to area 51
lamella_width = 9 ##width of umbrella field lamella in cells
umb_field=np.zeros((2,nxyz[0],nxyz[1],nxyz[2]))
##fill with negative values
umb_field.fill(-1)
##define target values
vals=np.array([0.1,0.9])

##quick function to help creating lamella structure
def flip(a,arr):
    if a==vals[0]:
        return arr[1]
    else:
        return arr[0]


A_val=vals[0]
B_val=vals[1]
count=0
for z in range(offset,nxyz[2]-offset):
    if count == lamella_width:
        A_val=flip(A_val,vals)
        B_val=flip(B_val,vals)
        count=0
    umb_field[0,offset:nxyz[0]-offset,offset,z] = A_val
    umb_field[1,offset:nxyz[0]-offset,offset,z] = B_val
    count+=1

    
e = "umbrella_field" in f
if e:
    del f["umbrella_field"]
e = "polyconversion" in f
if e:
    del f["polyconversion"]
##add umbrella field to f
dset_umb = f.create_dataset("umbrella_field", data=umb_field)
##copy polyconversion dataset to f
g.copy(g["polyconversion"],f,"polyconversion")
g.close()
f.close()