# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2023-02-25 13:13:07
# @Last Modified by:   Your name
# @Last Modified time: 2023-02-27 14:44:14


# Routine to set specific boundary structure using external field and to set area51
import h5py
import numpy as np

coordfile='coord.h5' ##file to be modified
##coordfile
f= h5py.File(coordfile, 'r+') 
nxyz=np.array(f['parameter/nxyz'])
lxyz=np.array(f['parameter/lxyz'])

##y periodicity of lamella in Re/2
lamella_period=1.5
num_lamella = lxyz[1]/lamella_period
##number of cells that define a lamella
lamella_discr=np.floor(nxyz[1]/num_lamella)


##file that contains polyconverison info


ext_field=np.zeros((2,nxyz[0],nxyz[1],nxyz[2]))

##define target values
vals=np.array([-10.0,10.0])

##quick function to help creating lamella structure
def flip(a,arr):
    if a==arr[0]:
        return arr[1]
    else:
        return arr[0]

##### FILL EXTERNAL FIELD


A_val=vals[0]
B_val=vals[1]
count=0
for y in range(nxyz[1]):
    if count == lamella_discr:
        A_val=flip(A_val,vals)
        B_val=flip(B_val,vals)
        count=0
    ##wall at x = 0
    ext_field[0,:,y,:] = A_val
    ext_field[1,:,y,:] = B_val
    count+=1
    ##wall at x = lx
    ext_field[0,:,y,:] = A_val
    ext_field[1,:,y,:] = B_val
    count+=1



    
e = "external_field" in f
if e:
    del f["external_field"]
##add umbrella field to f
dset_ext = f.create_dataset("external_field", data=ext_field)

f.close()