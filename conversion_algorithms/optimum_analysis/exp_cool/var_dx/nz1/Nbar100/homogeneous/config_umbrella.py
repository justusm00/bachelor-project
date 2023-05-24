# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2023-01-25 16:59:12
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-01 22:05:29
import h5py
import numpy as np
import sys

coordfile=sys.argv[1] ##file to be modified
##file that contains area51 and bead positions
f= h5py.File(coordfile, 'r+') 



lamella_width = int(sys.argv[2]) ##width of umbrella field lamella in cell
offset=0 ##to account for area51 (and maybe density drop next to it)


nxyz=np.array(f['parameter/nxyz'])
umb_field=np.zeros((2,nxyz[0],nxyz[1],nxyz[2]))


##fill umbrella field with 0.5
umb_field.fill(0.5)

    
e = "umbrella_field" in f
if e:
    del f["umbrella_field"]
e= "area51" in f
if e:
    del f["area51"]
##add umbrella field to f
dset_umb = f.create_dataset("umbrella_field", data=umb_field)

f.close()