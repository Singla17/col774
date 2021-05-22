# -*- coding: utf-8 -*-
"""a4_VNN.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1lUfe8OO_BaYpfiP9tD25PTMkzJjl67I2

Importing libraries and getting GPU node
"""

import os
import torch

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print("Using {}".format(device))

"""Dataset"""

import numpy as np
import pandas as pd
base = "/content/drive/MyDrive/"

from google.colab import drive
drive.mount('/content/drive')

prac = pd.read_csv(base+"train.csv",header=None)

print(len(prac))

at =prac.loc[0]
print(at[1:])
u = at[1:].to_numpy()
print(u)

from torch.utils.data import Dataset

class data(Dataset):
    def __init__(self, train):
        if train:
            self.data= pd.read_csv(base+"train.csv",header=None)                  # in this just define dataset of train and test after split into self.data
        else:
            self.data = pd.read_csv(base+"public_test.csv",header=None)

    def __getitem__(self, index):
        row= self.data.loc[index]
        target = int(row[0]);                                                          # gets data point sequentially
        x = row[1:].to_numpy()
        return x, target

    def __len__(self):
        return len(self.data)                                                      # gets nmber of datapoints

bsize = 128
inp_dims = 2304

"""VNN in pytorch"""

from torch import nn
import torch.nn.functional as func
from torchsummary import summary

class vnn(nn.Module):   # Inheritance in Python vnn inherits nn.Module 
  def __init__(self,inp_dims,dim_hidden,num_classes):   # constructor
    super(vnn, self).__init__()
    self.ip = nn.Linear(inp_dims,dim_hidden)
    self.op = nn.Linear(dim_hidden,num_classes)

  def forward(self,x):
    ol1 = func.relu(self.ip(x))
    output = func.softmax(self.op(ol1),dim=1)
    return output

hiddenlayer=100
classes =7 
model = vnn(inp_dims,100,7).to(device)
summary(model,(inp_dims,))

"""Training the model

"""

import torch
import torch.nn as nn
import torch.optim as opti
import torch.nn.functional as func
import torch.backends.cudnn as cudnn
import matplotlib.pyplot as plt
import numpy as np
from torch.utils.data import Dataset, DataLoader

def visualization(loss_arr,epo):
  x = np.linspace(1,epo,epo)
  plt.plot(x,loss_arr)

def training(lr, epochs):
  print('==> Preparing data..')
  trainset = data(train=True)
  trainloader = DataLoader(trainset, batch_size=128, shuffle=True, num_workers=2)
  testset = data(train=False)
  testloader = DataLoader(testset, batch_size=1, shuffle=True, num_workers=2)

  print('==> Building model..')
  nnet = vnn(inp_dims,100,7)
  nnet = nnet.to(device)
  if device == 'cuda':
      nnet = torch.nn.DataParallel(nnet)                                           ## for using multiple GPUs
      cudnn.benchmark = True
  
  criterion = nn.CrossEntropyLoss()
  optimizer = opti.SGD(nnet.parameters(), lr) 
  trainloss =[]
  for epoch in range(epochs):
    l= train_single_epoch(lr,criterion,optimizer,device,nnet,trainloader,128)
    trainloss.append(l)
    print("The loss was {}".format(l))
  visualization(trainloss,epochs)

  print("==> Testing the model..")
  print("Accuracy is found to be {}".format(test(testloader,criterion,nnet,device)))

def train_single_epoch(lr,criterion,optimizer,device,nnet,trainloader,bsize):
  nnet.train()                        ## a pytorch routine it is to turn ON some advanced layers which were turned OFF during testing  
  tloss =0
  for index,(x,y) in enumerate(trainloader):
    x= x.to(device).float()
    y = y.to(device).long()
    optimizer.zero_grad()          ## zeroing the gradients to nullify the effects of previous iterations
    pred_y = nnet(x)
    loss = criterion(pred_y,y)
    loss.backward()
    optimizer.step()
    tloss += loss.item() 
  return (tloss/index)

def test(testloader,criterion,nnet,device):
  nnet.eval()                     ## a pytorch routine it is to turn OFF some advanced layers during testing   
  correct = 0
  total = 0
  with torch.no_grad():          ## turn OFF autograd
    for index,(x,y) in enumerate(testloader):
      total = total + 1
      x= x.to(device).float()
      y = y.to(device).long()
      pred_ysf = nnet(x)
      pred_y = torch.max(pred_ysf,1)[1][0]
      if (pred_y) == (y) :
        correct = correct +1
  return (correct/total)

training(0.1,100)

"""Reference: https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html#test-the-network-on-the-test-data
https://pytorch.org/tutorials/beginner/blitz/neural_networks_tutorial.html#define-the-network

Image Processing techniques on the top of vanilla neural network
"""

from skimage.filters import gabor
from skimage.feature import hog

"""Filtering Datasets"""

df_train = pd.read_csv(base+"train.csv",header=None)
df_test = pd.read_csv(base+"public_test.csv",header=None)
iter = 1
x_final = np.zeros(4)
y_final = np.zeros(4)
for index, row in df_train.iterrows():
    x = row[1:]
    npx = x.to_numpy()
    npx = npx.reshape((48,48))
    fd,hog_img = hog(npx,visualize=True)
    filt_img = gabor(hog_img,frequency=0.6)
    arr = np.ravel(filt_img)
    use = np.zeros(1)
    use[0]=row[0]
    if iter==1:
      x_final = arr
      y_final = use
      iter = iter+1
    else:
      x_final = np.vstack([x_final, arr])
      y_final = np.vstack([y_final,use])
      iter = iter +1
    print(iter)
iter = 1
x_final_t = np.zeros(4)
y_final_t = np.zeros(4)
for index, row in df_test.iterrows():
    x = row[1:]
    npx = x.to_numpy()
    npx = npx.reshape((48,48))
    fd,hog_img = hog(npx,visualize=True)
    filt_img = gabor(hog_img,frequency=0.6)
    arr = np.ravel(filt_img)
    use = np.zeros(1)
    use[0]=row[0]
    if iter==1:
      x_final_t = arr
      y_final_t = use
      iter = iter+1
    else:
      x_final_t = np.vstack([x_final_t, arr])
      y_final_t = np.vstack([y_final_t,use])
      iter = iter+1
    print(iter)

print(np.shape(x_final))
print(np.shape(x_final_t))

from torch.utils.data import Dataset

class filter(Dataset):
    def __init__(self, train):
        if train:
            self.data= x_final               # in this just define dataset of train and test after split into self.data
            self.target = y_final
        else:
            self.data = x_final_t
            self.target = y_final_t            

    def __getitem__(self, index):
        target = int(self.target[index])                                                      # gets data point sequentially
        x = self.data[index]
        return x, target

    def __len__(self):
        return len(self.data)                                                      # gets nmber of datapoints

import torch
import torch.nn as nn
import torch.optim as opti
import torch.nn.functional as func
import torch.backends.cudnn as cudnn
import matplotlib.pyplot as plt
import numpy as np
from torch.utils.data import Dataset, DataLoader

def visualizationf(loss_arr,epo):
  x = np.linspace(1,epo,epo)
  plt.plot(x,loss_arr)

def trainingf(lr, epochs):
  print('==> Preparing data..')
  trainset = filter(train=True)
  trainloader = DataLoader(trainset, batch_size=128, shuffle=True, num_workers=2)
  testset = filter(train=False)
  testloader = DataLoader(testset, batch_size=1, shuffle=True, num_workers=2)

  print('==> Building model..')
  nnet = vnn(inp_dims*2,100,7)
  nnet = nnet.to(device)
  if device == 'cuda':
      nnet = torch.nn.DataParallel(nnet)                                           ## for using multiple GPUs
      cudnn.benchmark = True
  
  criterion = nn.CrossEntropyLoss()
  optimizer = opti.SGD(nnet.parameters(), lr) 
  trainloss =[]
  for epoch in range(epochs):
    l= train_single_epochf(lr,criterion,optimizer,device,nnet,trainloader,128)
    trainloss.append(l)
    print("The loss was {}".format(l))
  visualizationf(trainloss,epochs)

  print("==> Testing the model..")
  print("Accuracy is found to be {}".format(testf(testloader,criterion,nnet,device)))

def train_single_epochf(lr,criterion,optimizer,device,nnet,trainloader,bsize):
  nnet.train()                        ## a pytorch routine it is to turn ON some advanced layers which were turned OFF during testing  
  tloss =0
  for index,(x,y) in enumerate(trainloader):
    x= x.to(device).float()
    y = y.to(device).long()
    optimizer.zero_grad()          ## zeroing the gradients to nullify the effects of previous iterations
    pred_y = nnet(x)
    loss = criterion(pred_y,y)
    loss.backward()
    optimizer.step()
    tloss += loss.item() 
  return (tloss/index)

def testf(testloader,criterion,nnet,device):
  nnet.eval()                     ## a pytorch routine it is to turn OFF some advanced layers during testing   
  correct = 0
  total = 0
  with torch.no_grad():          ## turn OFF autograd
    for index,(x,y) in enumerate(testloader):
      total = total + 1
      x= x.to(device).float()
      y = y.to(device).long()
      pred_ysf = nnet(x)
      pred_y = torch.max(pred_ysf,1)[1][0]
      if (pred_y) == (y) :
        correct = correct +1
  return (correct/total)

trainingf(0.3,200)