# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2023-01-25 16:59:12
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-13 14:18:23
import h5py
import numpy as np
import sys

coordfile=sys.argv[1] ##file to be modified
delta_phi=float(sys.argv[2]) ##delta phi
lamella_width=int(sys.argv[3]) ##lamella width in number of cells 
##file that contains area51 and bead positions


f= h5py.File(coordfile, 'r+') 
e = "umbrella_field" in f
if e:
    del f["umbrella_field"]
e= "area51" in f
if e:
    del f["area51"]


n=lamella_width
offset=1 ##to account for area51 (and maybe density drop next to it)




nxyz=np.array(f['parameter/nxyz'])
umb_field=np.zeros((2,nxyz[0],nxyz[1],nxyz[2]))
area51=np.zeros((nxyz[0],nxyz[1],nxyz[2])) #need to adjust area51 too since system size is not constant
##fill umbrella field with negative values
umb_field.fill(-1)
# fill area51
area51[:,:,-1]=1
area51[:,:,0]=1
area51[0,:,:]=1
area51[-1,:,:]=1
area51[:,0,:]=1
area51[:,-1,:]=1


##define target values
vals=np.array([0.5-delta_phi,0.5+delta_phi])

#number of lamellae
m=int((nxyz[0]-2*offset)/n)
# Use nested for loops to assign the lamella-like values
for i in range(m):
    if i % 2 == 0:  
        umb_field[0,offset+i*n:offset+(i+1)*n, offset, offset:nxyz[2]-offset] = vals[0]
        umb_field[1,offset+i*n:offset+(i+1)*n, offset, offset:nxyz[2]-offset] = vals[1]    
    else:
        umb_field[0,offset+i*n:offset+(i+1)*n, offset, offset:nxyz[2]-offset] = vals[1]
        umb_field[1,offset+i*n:offset+(i+1)*n, offset, offset:nxyz[2]-offset] = vals[0]   



##add umbrella field to f
dset_umb = f.create_dataset("umbrella_field", data=umb_field)
dset_area51 = f.create_dataset("area51", data=area51)

f.close()