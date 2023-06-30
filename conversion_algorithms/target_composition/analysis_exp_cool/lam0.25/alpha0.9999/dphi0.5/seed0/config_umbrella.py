# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2023-01-25 16:59:12
# @Last Modified by:   Your name
# @Last Modified time: 2023-06-29 18:31:39
import h5py
import numpy as np
import sys

#routine to adjust umbrella field, area51 and minimum annealing temperature
##usage: python3 config_umbrella.py <coordfile> <delta_phi>  <total_density> <alpha> <Tmax>

coordfile=sys.argv[1] ##file to be modified
delta_phi=float(sys.argv[2]) ##delta phi
total_density=float(sys.argv[3])
alpha=float(sys.argv[4])
Tmax=float(sys.argv[5])
Tmin=1e-4
##file that contain area51 and bead positions
f= h5py.File(coordfile, 'r+') 
e = "umbrella_field" in f
if e:
    del f["umbrella_field"]
e = "external_field" in f
if e:
    del f["external_field"]
e= "area51" in f
if e:
    del f["area51"]


lamella_width = 1##width of umbrella field lamella in cell
n=lamella_width
offset=1 ##to account for area51 (and maybe density drop next to it)




nxyz=np.array(f['parameter/nxyz'])
lxyz=np.array(f['parameter/lxyz'])
dxyz=lxyz/nxyz #spacing
#adjust lxyz to account for area 51
lxyz[1]=lxyz[1]-2*offset*dxyz[1]
V=np.prod(lxyz)
N=int(f['parameter/reference_Nbeads'][()]) 
##number of polymers
n_polym=int(f['parameter/n_polymers'][()]) 
rho0=n_polym*N/V
#beads per cell
rhoc=rho0*np.prod(dxyz)
print(f"Tmax:{Tmax}")
print(f"Tmin:{Tmin}")
print(f"alpha:{alpha}")






umb_field=np.zeros((2,nxyz[0],nxyz[1],nxyz[2]))
ext_field=np.zeros((2,nxyz[0],nxyz[1],nxyz[2]))
area51=np.zeros((nxyz[0],nxyz[1],nxyz[2])) #need to adjust area51 too since system size is not constant
##fill umbrella field with negative values
umb_field.fill(-1)
# fill area51
area51[:,0,:]=1
area51[:,-1,:]=1


##define target density values
vals=np.array([0.5-delta_phi,0.5+delta_phi])*total_density
print(vals)

#number of lamellae
m=int((nxyz[0])/n)
# Use nested for loops to assign the  lamellar-like values
for i in range(m):
    if i % 2 == 0:  
        umb_field[0,i*n:(i+1)*n, offset, :] = vals[0]
        umb_field[1,i*n:(i+1)*n, offset, :] = vals[1]
    else:
        umb_field[0,i*n:(i+1)*n, offset, :] = vals[1]
        umb_field[1,i*n:(i+1)*n, offset, :] = vals[0]





##add data to coordfile
dset_umb = f.create_dataset("umbrella_field", data=umb_field)
#dset_fext=f.create_dataset("external_field", data=ext_field)
dset_area51 = f.create_dataset("area51", data=area51)

e = "parameter/Tmin" in f
if e:
    del f["parameter/Tmin"]
dset_Tmin = f.create_dataset("parameter/Tmin", data=np.array([Tmin]))
e = "parameter/Tmax" in f
if e:
    del f["parameter/Tmax"]
dset_Tmax = f.create_dataset("parameter/Tmax", data=np.array([Tmax]))
e = "parameter/alpha" in f
if e:
    del f["parameter/alpha"]
dset_alpha = f.create_dataset("parameter/alpha", data=np.array([alpha]))


f.close()