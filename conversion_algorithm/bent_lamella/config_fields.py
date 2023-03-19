# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2023-02-25 13:13:07
# @Last Modified by:   Your name
# @Last Modified time: 2023-03-14 21:28:25


# Routine to set specific boundary structure using external field and to set area51
import h5py
import numpy as np

coordfile='coord.h5' ##file to be modified
conversion_file='coord_conversion.h5' #file to read polyconversion from
##file that contains area51 and bead positions
f= h5py.File(coordfile, 'r+') 
# file to read polyconversion info from
g=h5py.File(conversion_file, 'r+')
##file that contains polyconverison info
nxyz=np.array(f['parameter/nxyz'])
lxyz=np.array(f['parameter/lxyz'])

lamella_width=100/142 ##width of equilibrium lamella in Re
y_discretization=lxyz[1]/nxyz[1]
lamella_discretization=np.ceil(lamella_width/y_discretization) ##how many cells a lamella has
lamella_xdim = 2##width of umbrella field lamella in x direction


umb_field=np.zeros((2,nxyz[0],nxyz[1],nxyz[2]))

##define target values
vals=np.array([0.1,0.9])

##quick function to help creating lamella structure
def flip(a,arr):
    if a==arr[0]:
        return arr[1]
    else:
        return arr[0]

##### FILL UMBRELLA FIELD


A_val=vals[0]
B_val=vals[1]
count=0
for y in range(nxyz[1]):
    if count == lamella_discretization:
        A_val=flip(A_val,vals)
        B_val=flip(B_val,vals)
        count=0
    ##wall at x = 0
    umb_field[0,0:lamella_xdim,y,:] = A_val
    umb_field[1,0:lamella_xdim,y,:] = B_val
    ##wall at x = lx
    umb_field[0,(-1-lamella_xdim):-1,y,:] = A_val
    umb_field[1,(-1-lamella_xdim):-1,y,:] = B_val
    count+=1



    
e = "umbrella_field" in f
if e:
    del f["umbrella_field"]
e= "external_field" in f
if e:
    del f["external_field"]
e = "polyconversion" in f
if e:
    del f["polyconversion"]
# sa parameters have to be added too 
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
dset_Tmin = f.create_dataset("parameter/Tmin", data=np.array([0.01]))
dset_Tmax = f.create_dataset("parameter/Tmax", data=np.array([0.001]))
dset_Talpha = f.create_dataset("parameter/alpha", data=np.array([0.85]))
g.copy(g["polyconversion"],f,"polyconversion")

f.close()
g.close()