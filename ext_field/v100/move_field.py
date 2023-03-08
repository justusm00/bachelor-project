# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2023-02-25 13:13:07
# @Last Modified by:   Your name
# @Last Modified time: 2023-02-28 11:50:18


# Routine to move external field to simulate time dependency
import h5py
import numpy as np
from copy import deepcopy

coordfile='end.h5' ##file to be modified
##file that contains area51 and bead positions
f= h5py.File(coordfile, 'r+') 
##file that contains polyconverison info
nxyz=np.array(f['parameter/nxyz'])
lxyz=np.array(f['parameter/lxyz'])
ext_field=np.array(f['external_field'])
ext_field_cpy=deepcopy(ext_field)

## move external field up one grid point

ext_field[0,:,0,:] = ext_field_cpy[0,:,-1,:]
ext_field[1,:,0,:] = ext_field_cpy[1,:,-1,:]
for y in range(1,nxyz[1]):
    ext_field[0,:,y,:] = ext_field_cpy[0,:,y-1,:]
    ext_field[1,:,y,:] = ext_field_cpy[1,:,y-1,:]


e = "external_field" in f
if e:
    del f["external_field"]
##save new external field
dset_ext = f.create_dataset("external_field", data=ext_field)

f.close()