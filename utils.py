from __future__ import print_function
import os, sys, gzip, torch, time
import torch.nn as nn
import numpy as np
import scipy.misc
import imageio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from torchvision import datasets, transforms
from torch.utils.data import Dataset, DataLoader
from PIL import Image

import pdb

def load_mnist(dataset, dataroot_dir="./data"):
    data_dir = os.path.join(dataroot_dir, dataset)

    def extract_data(filename, num_data, head_size, data_size):
        with gzip.open(filename) as bytestream:
            bytestream.read(head_size)
            buf = bytestream.read(data_size * num_data)
            data = np.frombuffer(buf, dtype=np.uint8).astype(np.float)
        return data

    data = extract_data(data_dir + '/train-images-idx3-ubyte.gz', 60000, 16, 28 * 28)
    trX = data.reshape((60000, 28, 28, 1))

    data = extract_data(data_dir + '/train-labels-idx1-ubyte.gz', 60000, 8, 1)
    trY = data.reshape((60000))

    data = extract_data(data_dir + '/t10k-images-idx3-ubyte.gz', 10000, 16, 28 * 28)
    teX = data.reshape((10000, 28, 28, 1))

    data = extract_data(data_dir + '/t10k-labels-idx1-ubyte.gz', 10000, 8, 1)
    teY = data.reshape((10000))

    trY = np.asarray(trY).astype(np.int)
    teY = np.asarray(teY)

    X = np.concatenate((trX, teX), axis=0)
    y = np.concatenate((trY, teY), axis=0).astype(np.int)

    seed = 547
    np.random.seed(seed)
    np.random.shuffle(X)
    np.random.seed(seed)
    np.random.shuffle(y)

    y_vec = np.zeros((len(y), 10), dtype=np.float)
    for i, label in enumerate(y):
        y_vec[i, y[i]] = 1

    X = X.transpose(0, 3, 1, 2) / 255.
    # y_vec = y_vec.transpose(0, 3, 1, 2)

    X = torch.from_numpy(X).type(torch.FloatTensor)
    y_vec = torch.from_numpy(y_vec).type(torch.FloatTensor)
    return X, y_vec

def CustomDataLoader(path, transform, batch_size, shuffle):
    # transform = transforms.Compose([
    #     transforms.CenterCrop(160),
    #     transform.Scale(64)
    #     transforms.ToTensor(),
    #     transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
    # ])

    # data_dir = 'data/celebA'  # this path depends on your computer
    dset = datasets.ImageFolder(path, transform)
    data_loader = torch.utils.data.DataLoader(dset, batch_size, shuffle)

    return data_loader

class MultiPie( Dataset ):
	def __init__( self, root_dir, transform=None, cam_ids=None):
		self.filenames = []
		self.root_dir = root_dir
		self.transform = transform

		#cam_ids = [10, 41, 50, 51, 80, 81, 90, 110, 120, 130, 140, 190, 191, 200, 240]
		#cam_ids = [41, 50, 51, 80, 90, 130, 140, 190, 200]
		if cam_ids is None:
			cam_ids = [200, 190, 41, 50, 51, 140, 130, 80, 90]
		self.cam_map = {}
		for i, cam in enumerate(cam_ids):
			self.cam_map[cam] = i

		print('Loading MultiPie metadata...', end='')
		sys.stdout.flush()
		time_start = time.time()

		fname_cache = 'cache_multipie.txt'
		if os.path.exists(fname_cache):
			self.filenames = open(fname_cache).read().splitlines()
			print( 'restored from {}'.format(fname_cache) )
		else:
			path = os.path.join( root_dir, 'Multi-Pie', 'data' )
			self.filenames = [os.path.join(dirpath,f) for dirpath, dirnames, files in os.walk(path)
							for f in files if f.endswith('.png') ]
	
			print('{:.0f}sec, {} images found.'.format( time.time()-time_start, len(self.filenames)))
	
			f = open(fname_cache, 'w')
			for fname in self.filenames:
				f.write(fname+'\n')
			f.close()
			print( 'cached in {}'.format(fname_cache) )

		# filtering : 9 cams and 200 subjects
		self.filenames = [ f for f in self.filenames 
							if int(os.path.basename(f)[10:13]) in cam_ids ]
							#if int(os.path.basename(f)[10:13]) in cam_ids and int(os.path.basename(f)[:3]) < 201 ]
#		print('shuffling...', end='')
#		sys.stdout.flush()
#		time_start = time.time()
#		seed = 547
#		np.random.seed(seed)
#		shuffler = np.arange( len(filenames) )
#		np.random.shuffle(shuffler)
#
#		shuffler = shuffler.tolist()
#		self.filenames = [filenames[s] for s in shuffler]
#		print('{:.0f}sec'.format( time.time()-time_start))
#		sys.stdout.flush()
		

	def __len__( self ):
		return len( self.filenames )
	
	def __getitem__( self, idx ):
		basename = os.path.basename( self.filenames[idx] )
		identity, sessionNum, recordingNum, pose, illum =  basename[:-4].split('_')
		image = Image.open( self.filenames[idx] ).convert('L')
		pose = self.cam_map[int(pose)]
		if self.transform:
			image = self.transform(image)
		labels = { 'id': int(identity),
					'pose': pose,
					'illum': int(illum)}
		return image, labels 

def print_network(net):
    num_params = 0
    for param in net.parameters():
        num_params += param.numel()
    print(net)
    print('Total number of parameters: %d' % num_params)

def save_images(images, size, image_path):
    return imsave(images, size, image_path)

def imsave(images, size, path):
    image = np.squeeze(merge(images, size))
    return scipy.misc.imsave(path, image)

def merge(images, size):
    h, w = images.shape[1], images.shape[2]
    if (images.shape[3] in (3,4)):
        c = images.shape[3]
        img = np.zeros((h * size[0], w * size[1], c))
        for idx, image in enumerate(images):
            i = idx % size[1]
            j = idx // size[1]
            img[j * h:j * h + h, i * w:i * w + w, :] = image
        return img
    elif images.shape[3]==1:
        img = np.zeros((h * size[0], w * size[1]))
        for idx, image in enumerate(images):
            i = idx % size[1]
            j = idx // size[1]
            img[j * h:j * h + h, i * w:i * w + w] = image[:,:,0]
        return img
    else:
        raise ValueError('in merge(images,size) images parameter ''must have dimensions: HxW or HxWx3 or HxWx4')

def generate_animation(path, num):
    images = []
    for e in range(num):
        img_name = path + '_epoch%03d' % (e+1) + '.png'
        images.append(imageio.imread(img_name))
    imageio.mimsave(path + '_generate_animation.gif', images, fps=5)

def loss_plot(hist, path = 'Train_hist.png', model_name = ''):
    x = range(len(hist['D_loss']))

    y1 = hist['D_loss']
    y2 = hist['G_loss']

    plt.plot(x, y1, label='D_loss')
    plt.plot(x, y2, label='G_loss')

    plt.xlabel('Iter')
    plt.ylabel('Loss')

    plt.legend(loc=4)
    plt.grid(True)
    plt.tight_layout()

    path = os.path.join(path, model_name + '_loss.png')

    plt.savefig(path)

    plt.close()

def initialize_weights(net):
    for m in net.modules():
        if isinstance(m, nn.Conv2d):
            m.weight.data.normal_(0, 0.02)
            m.bias.data.zero_()
        elif isinstance(m, nn.ConvTranspose2d):
            m.weight.data.normal_(0, 0.02)
            m.bias.data.zero_()
        elif isinstance(m, nn.Linear):
            m.weight.data.normal_(0, 0.02)
            m.bias.data.zero_()
