# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2023-01-25 16:59:12
# @Last Modified by:   Your name
# @Last Modified time: 2023-06-14 16:14:02
import h5py
import numpy as np
import sys

#routine to adjust umbrella field, area51 and minimum annealing temperature
##usage: python3 config_umbrella.py <coordfile> <delta_phi> <SA> <total_density>

coordfile=sys.argv[1] ##file to be modified
delta_phi=float(sys.argv[2]) ##delta phi
sa =int(sys.argv[3]) 
total_density=float(sys.argv[4])
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


lamella_width = 5##width of umbrella field lamella in cell
n=lamella_width
offset=1 ##to account for area51 (and maybe density drop next to it)




nxyz=np.array(f['parameter/nxyz'])
lxyz=np.array(f['parameter/lxyz'])
dxyz=lxyz/nxyz #spacing
#adjust lxyz to account for area 51
lxyz=lxyz-2*offset*dxyz
V=np.prod(lxyz)
N=int(f['parameter/reference_Nbeads'][()]) 
##number of polymers
n_polym=int(f['parameter/n_polymers'][()]) 
rho0=n_polym*N/V
#beads per cell
rhoc=rho0*np.prod(dxyz)
Tmin=0.1*(1/rhoc**2)
#Tmin=0.001
if(sa==1):
    Tmax=20*Tmin
else:
    Tmax=-1
Tmax=0.1
alpha=0.01*Tmin
print(f"Tmax:{Tmax}")
print(f"Tmin:{Tmin}")
print(f"alpha:{alpha}")
print(f"1/rhoc^2:{(1/rhoc**2)}")






umb_field=np.zeros((2,nxyz[0],nxyz[1],nxyz[2]))
ext_field=np.zeros((2,nxyz[0],nxyz[1],nxyz[2]))
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


##define target density values
vals=np.array([0.5-delta_phi,0.5+delta_phi])*total_density
print(vals)

#number of lamellae
m=int((nxyz[0]-2*offset)/n)
# Use nested for loops to assign the  lamellar-like values
for i in range(m):
    if i % 2 == 0:  
        umb_field[0,offset+i*n:offset+(i+1)*n, offset, offset:nxyz[2]-offset] = vals[0]
        umb_field[1,offset+i*n:offset+(i+1)*n, offset, offset:nxyz[2]-offset] = vals[1]  
        ext_field[0,offset+i*n:offset+(i+1)*n, offset, offset:nxyz[2]-offset] = vals[1]*1000
        ext_field[1,offset+i*n:offset+(i+1)*n, offset, offset:nxyz[2]-offset] = vals[0]*1000
    else:
        umb_field[0,offset+i*n:offset+(i+1)*n, offset, offset:nxyz[2]-offset] = vals[1]
        umb_field[1,offset+i*n:offset+(i+1)*n, offset, offset:nxyz[2]-offset] = vals[0]
        ext_field[0,offset+i*n:offset+(i+1)*n, offset, offset:nxyz[2]-offset] = vals[0]*1000
        ext_field[1,offset+i*n:offset+(i+1)*n, offset, offset:nxyz[2]-offset] = vals[1]*1000




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