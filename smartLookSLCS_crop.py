#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug  9 10:16:54 2018
DOWNLOOKING
Saves downlooked ifgs in the respective ifg directories.

FILTERING
work in progress

@author: kdm95
"""

import numpy as np
import isceobj
from matplotlib import pyplot as plt
from mpl_toolkits.basemap import Basemap
import cv2
import os

filterFlag = False
filterStrength = '0.3'
nblocks = 1

#from mroipac.filter.Filter import Filter
params = np.load('params.npy',allow_pickle=True).item()
locals().update(params)
# geom = np.load('geom.npy',allow_pickle=True).item()
seaLevel=-10
#locals().update(geom)
#params['slcdir'] = '/data/kdm95/Delta/p42/merged/SLC_VV'
#np.save('params.npy',params)

tsdir = params['tsdir']

cropymin = 298
cropymax = 1784
cropxmin = 2868
cropxmax = 6352

nyl2 = cropymax-cropymin
nxl2 = cropxmax-cropxmin
ymin = 0 
ymax = nyl2

# Creat window and downlooking vectors
win1 =np.ones((params['alks'],params['rlks']))
win=win1/sum(win1.flatten())
rangevec=np.arange(0,nxl) * params['rlks']
azvec=np.arange(0,nyl) * params['alks']
yy,xx= np.meshgrid(azvec,rangevec,sparse=False, indexing='ij')
y=yy.flatten()
x=xx.flatten()
del(xx,yy)

# Load the gamma0 file
f = params['tsdir'] + '/gamma0.int'
intImage = isceobj.createIntImage()
intImage.load(f + '.xml')
gamma0= intImage.memMap()[:,:,0] 
gamma0=gamma0.copy() # mmap is readonly, so we need to copy it.


if not os.path.isfile('gam.npy'):
    # Perform smart_looks first on gamma0
    gam=gamma0.copy() # mmap is readonly, so we need to copy it.
    #gam[np.where(gam==0)]=np.nan
    gam = cv2.filter2D(gam,-1, win)
    gam = np.reshape(gam[y,x],(nyl,nxl))
    gam[np.isnan(gam)] = 0
    # Save gamma0 file
    out = isceobj.createIntImage() # Copy the interferogram image from before
    out.dataType = 'FLOAT'
    out.filename = params['tsdir'] + '/gamma0_lk.int'
    out.width = nxl
    out.length = nyl
    out.dump(out.filename + '.xml') # Write out xml
    gam.tofile(out.filename) # Write file out
    out.renderHdr()
    out.renderVRT()
    gam[geom['hgt_ifg'] < seaLevel] = 0
    gamCrop = gam[cropymin:cropymax,cropxmin:cropxmax]
    np.save('gam.npy',gamCrop)
    del(gam)
else: 
    print('gam.npy already exists')



if not os.path.isdir(params['intdir']):
    os.system('mkdir ' + params['intdir'])

msk_filt = cv2.filter2D(gamma0,-1, win)
pair = params['pairs'][0]

for pair in params['pairs']: #loop through each ifg and save to 
    if not os.path.isdir(params['intdir'] + '/' + pair):
        os.system('mkdir ' + params['intdir']+ '/' + pair)
    if not os.path.isfile(params['intdir'] + '/' + pair + '/fine_lk_filt.int'):
        print('working on ' + pair)
        
        #Open a file to save stuff to
        out = isceobj.createImage() # Copy the interferogram image from before
        out.dataType = 'CFLOAT'
        out.filename = params['intdir'] + '/' + pair + '/fine_lk.int'
        out.width = nxl2
        out.length = nyl2
        out.dump(out.filename + '.xml') # Write out xml
        fid=open(out.filename,"ab+")
        
        # open a cor file too
        outc = isceobj.createImage() # Copy the interferogram image from before
        outc.dataType = 'FLOAT'
        outc.filename = params['intdir'] + '/' + pair + '/cor_lk.r4'
        outc.width = nxl2
        outc.length = nyl2
        outc.dump(outc.filename + '.xml') # Write out xml
        fidc=open(outc.filename,"ab+")
        
        # break it into blocks
        for kk in np.arange(0,nblocks):
            print(str(kk))
            idy = int(np.floor(ny/nblocks))
            start = int(kk*idy)
            stop = start+idy+1
            rangevec=np.arange(0,nxl) * params['rlks']
            idl = int(np.floor(params['nyl']/nblocks))
            azvec=np.arange(0,idl) * params['alks']
            
            yy,xx= np.meshgrid(azvec,rangevec,sparse=False, indexing='ij')
            y=yy.flatten()
            x=xx.flatten()            
            d2 = pair[9:]
            d = pair[0:8]
            #load ifg real and imaginary parts
            f = params['slcdir'] +'/'+ d + '/' + d + '.slc.full'
    #        os.system('fixImageXml.py -i ' + f + ' -f')
    
            slcImage = isceobj.createSlcImage()
            slcImage.load(f + '.xml')
            slc1 = slcImage.memMap()[start:stop,:,0]
            f = params['slcdir'] +'/'+ d2 + '/' + d2 + '.slc.full'
    #        os.system('fixImageXml.py -i ' + f + ' -f')
    
            slcImage = isceobj.createSlcImage()
            slcImage.load(f + '.xml')
            slc2 = slcImage.memMap()[start:stop,:,0]
            ifg = np.multiply(slc1,np.conj(slc2))
            
            del(slc1,slc2)
            
            ifg_real = np.real(ifg)
            ifg_imag = np.imag(ifg)
            
            del(ifg)
        
            ifg_real_filt0 = cv2.filter2D(ifg_real,-1, win)
            ifg_real = ifg_real * gamma0[start:stop,:]
            ifg_real_filt = cv2.filter2D(ifg_real,-1, win)
            del(ifg_real)
            rea_lk = np.reshape((ifg_real_filt/msk_filt[start:stop,:])[y,x],(idl,params['nxl']))
            del(ifg_real_filt)
    
            ifg_imag_filt0 = cv2.filter2D(ifg_imag,-1, win)
            ifg_imag = ifg_imag * gamma0[start:stop,:]
            ifg_imag_filt = cv2.filter2D(ifg_imag,-1, win)
            del(ifg_imag)
            ima_lk = np.reshape((ifg_imag_filt/msk_filt[start:stop,:])[y,x],(idl,params['nxl']))
            del(ifg_imag_filt)
            
    #        phs_lk = np.arctan2(ima_lk, rea_lk)
    #        phs_lk[np.isnan(phs_lk)] = 0
    #        phs_lk[geom['hgt_ifg'] < seaLevel] = 0
            cpx = ima_lk*1j + rea_lk
            cpx[np.isnan(cpx)] = 0
#            cpx[geom['hgt_ifg'] < seaLevel] = 0
                    # Save downlooked ifg
    
#            cpx.tofile(of) # Write file out
            cpx = cpx[cropymin:cropymax,cropxmin:cropxmax]
            cpx = cpx.copy(order='C')
            fid.write(cpx)
            
            
            cor_lk = np.log(  np.abs(  (rea_lk+(1j*ima_lk)).astype(np.complex64)) )
            cor_lk /= cor_lk[~np.isnan(cor_lk)].max()
            cor_lk[np.isinf(cor_lk)] = 0
            cor_lk[np.isnan(cor_lk)] = 0
#            cor_lk[geom['hgt_ifg'] < seaLevel] = 0
            cor_lk = cor_lk[cropymin:cropymax,cropxmin:cropxmax]
            cor_lk = cor_lk.copy(order='C')
            fidc.write(cor_lk)
        
        out.renderHdr()
        out.renderVRT()  
        outc.renderHdr()
        outc.renderVRT() 
        fid.close()
        fidc.close()

        if filterFlag:
            offilt =  params['intdir'] + '/' + pair + '/fine_lk_filt.int'
            command = 'python /home/kdm95/Software/isce2/contrib/stack/topsStack/FilterAndCoherence.py -i ' + out.filename + ' -f ' +  offilt + ' -s ' + filterStrength
            os.system(command)

        
geom = {}
geom['lon_ifg'] = lon_ifg[cropymin:cropymax,cropxmin:cropxmax] 
geom['lat_ifg'] = lat_ifg[cropymin:cropymax,cropxmin:cropxmax] 
geom['hgt_ifg'] = hgt_ifg[cropymin:cropymax,cropxmin:cropxmax] 
np.save('geom.npy',geom)

params['nxl'] =          nxl2
params['nyl'] =          nyl2
params['lon_bounds'] =   lon_bounds
params['lat_bounds'] =   lat_bounds
params['ymin'] =         ymin
params['ymax'] =         ymax
params['xmin'] =         xmin
params['xmax'] =         xmax
np.save('params.npy',params)

# Downlook geom files this way too

# Get bounding coordinates (Frame)
#f_lon = mergeddir + '/geom_master/lon.rdr.full'
#f_lat = mergeddir + '/geom_master/lat.rdr.full'
#f_hgt = mergeddir + '/geom_master/hgt.rdr.full'
#
#Image = isceobj.createImage()
#Image.load(f_lon + '.xml')
#lon_ifg2 = Image.memMap()[:,:,0].copy().astype(np.float32)
#lon_lk2 = cv2.filter2D(lon_ifg2,-1, win)
#lonlk = np.reshape(lon_lk2[y,x],(params['nyl'],params['nxl']))
#
#
#Image = isceobj.createImage()
#Image.load(f_lat + '.xml')
#lat_ifg2 = Image.memMap()[:,:,0].copy().astype(np.float32)
#lat_lk2 = cv2.filter2D(lat_ifg2,-1, win)
#latlk = np.reshape(lat_lk2[y,x],(params['nyl'],params['nxl']))
#
#Image = isceobj.createImage()
#Image.load(f_hgt + '.xml')
#hgt_ifg2 = Image.memMap()[:,:,0].copy().astype(np.float32)
#hgt_lk2 = cv2.filter2D(hgt_ifg2,-1, win)
#hgtlk = np.reshape(hgt_lk2[y,x],(params['nyl'],params['nxl']))
#
#geom = {}
#geom['lon_ifg'] = lonlk
#geom['lat_ifg'] = latlk
#geom['hgt_ifg'] = hgtlk
#np.save('geom.npy',geom)
