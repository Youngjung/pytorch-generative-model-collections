#
# handling voxel data of ShapeNet dataset.
#

import sys, os, glob
import numpy as np
import scipy.ndimage as nd
import h5py
import binvox_rw
import struct

import pdb

def convert(s):
	i = int(s, 16)                   # convert from hex to a Python int
	cp = pointer(c_int(i))           # make this into a c integer
	fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float 
	return fp.contents.value         # dereference the pointer, get the float

def read_bnt(path, shape=(128,128,128)):
	with open(path, 'rb') as f:
		nrows	= struct.unpack('h',f.read(2))[0]
		ncols	= struct.unpack('h',f.read(2))[0]
		zmin	= struct.unpack('d',f.read(8))[0]
		length	= struct.unpack('h',f.read(2))[0]
		imfile	= f.read(length)
		length	= struct.unpack('I',f.read(4))[0]
		pcl		= struct.unpack('d'*length,f.read(length*8))
		pcl		= np.array(pcl).reshape(5,length/5).transpose()
	
	xmax = 200 
	xmin = -200
	ymax = 200
	ymin = -200
	zmax = 300
	zmin = -300
	raw_shape = (xmax-xmin+1,ymax-ymin+1,zmax-zmin+1)
	voxel_data = np.zeros(raw_shape)
	for i in range(pcl.shape[0]):
		x,y,z,_,_ = pcl[i]
		try:
			voxel_data[int(x)-xmin,int(y)-ymin,int(z)-zmin] = 1
		except:
			print( x,y,z )
			print( int(x)-xmin,int(y)-ymin,int(z)-zmin )
	if shape is not None and voxel_data.shape != shape:
		voxel_data = resize(voxel_data, shape)
	return voxel_data, nrows, ncols, imfile

def read_h5(path):
	"""
	read .h5 file
	"""
	f = h5py.File(path, 'r')
	voxel = f['data'][:]
	f.close()

	return voxel

def resize(voxel, shape, square=True):
	"""
	resize voxel shape
	"""
	if square:
		ratio = float(shape[0]) / voxel.shape[0]
	else:
		ratio = [float(s)/v for (s,v) in zip(shape,voxel.shape)]
	voxel = nd.zoom(voxel,
			ratio,
			order=1, 
			mode='nearest')
	voxel[np.nonzero(voxel)] = 1.0
	return voxel

def read_binvox(path, shape=(64,64,64), fix_coords=True):
	"""
	read voxel data from .binvox file
	"""
	with open(path, 'rb') as f:
		voxel = binvox_rw.read_as_3d_array(f, fix_coords)
	
	voxel_data = voxel.data.astype(np.float)
	if shape is not None and voxel_data.shape != shape:
		voxel_data = resize(voxel.data.astype(np.float64), shape)

	return voxel_data

def write_binvox(data, path):
	"""
	write out voxel data
	"""
	data = np.rint(data).astype(np.uint8)
	dims = data.shape
	translate = [0., 0., 0.]
	scale = 1.0
	axis_order = 'xyz'
	v = binvox_rw.Voxels( data, dims, translate, scale, axis_order)

	with open(path, 'bw') as f:
		v.write(f)

def read_all_binvox(directory):
	"""
	read all .binvox files in the direcotry
	"""
	input_files = [f for f in glob.glob(directory + "/**/*.binvox", recursive=True)]

	data = np.array([read_binvox(path) for path in input_files])
	n, w, h, d = data.shape

	return data.reshape(n, w, h, d, 1)

def main():
	data = read_all_binvox('./data')
	print(data.shape)

if __name__ == '__main__':
	main()
