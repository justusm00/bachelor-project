# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2023-01-25 16:59:12
# @Last Modified by:   Your name
# @Last Modified time: 2023-02-09 13:50:26
import h5py
import numpy as np
import sys

coordfile=sys.argv[1] ##file to be modified
umbfile = 'coord_umb.h5' ##file that contains polyconversion info
##file that contains area51 and bead positions
f= h5py.File(coordfile, 'r+') 
##file that contains polyconverison info
g=h5py.File(umbfile, 'r+')


lamella_width = int(sys.argv[2]) ##width of umbrella field lamella in cell
offset=2 ##to account for area51 (and maybe density drop next to it)


nxyz=np.array(f['parameter/nxyz'])
umb_field=np.zeros((2,nxyz[0],nxyz[1],nxyz[2]))
##fill with negative values
umb_field.fill(-1)
##define target values
vals=np.array([0.1,0.9])

##quick function to help creating lamella structure
def flip(a,arr):
    if a==arr[0]:
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
e = "parameter/Tmin" in f
if e:
    del f["parameter/Tmin"]
e = "parameter/Tmax" in f
if e:
    del f["parameter/Tmax"]
e = "parameter/alpha" in f
if e:
    del f["parameter/alpha"] 
##add umbrella field to f
dset_umb = f.create_dataset("umbrella_field", data=umb_field)
dset_Tmin = f.create_dataset("parameter/Tmin", data=np.array(g['parameter/Tmin']))
dset_Tmax = f.create_dataset("parameter/Tmax", data=np.array(g['parameter/Tmax']))
dset_Talpha = f.create_dataset("parameter/alpha", data=np.array(g['parameter/alpha']))
##copy polyconversion dataset to f
Tmin=f["parameter/Tmin"]
Tmax=f['parameter/Tmax']
alpha=f['parameter/alpha']
Tmin[:]=g['parameter/Tmin']
Tmax[:]=g['parameter/Tmax']
alpha[:]=g['parameter/alpha']
g.copy(g["polyconversion"],f,"polyconversion")

g.close()
f.close()