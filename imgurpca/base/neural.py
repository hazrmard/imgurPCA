from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
import numpy as np


class FeedForwardNN(object):

    def __init__(self, ninputs, nlayers, maxlayersize, batchsize=1, lr=0.1):
        self.ninputs = ninputs                   # number of input neurons
        self.nlayers = nlayers                 # number of hidden layers
        self.maxlayersize = maxlayersize       # max no. of neurons in a single layer

        self.layers = np.zeros((maxlayersize, nlayers+1))      # layer values (2x2 array, each col. a layer)
        self.sigmoids = np.zeros((maxlayersize, nlayers+1))    # stimuli (output of sigmoids)
        self.biases = np.zeros((maxlayersize, nlayers+1))     # biases for each neuron
        self.weights = [None] * (nlayers+1)                    # input weights (nhlayers+1 2x2 arrays)
        for i in range(1, nlayers+1):
            self.weights[i] = np.zeros((maxlayersize, maxlayersize))
        self.weights[0] = np.ones((maxlayersize, ninputs))            # input weights

        self._error = np.zeros(self.maxlayersize)
        self._batchsize = batchsize
        self.lr = lr        # learning rate


    def feed_forward(self, example, nox=False):
        i = example[0]
        o = example[1]
        self.layers[:,0] = np.dot(self.weights[0],i) + self.biases[:,0]
        self.sigmoids[:,0] = 1 / (1 + np.exp(-self.layers[:,0]))
        for j in range(1,self.nlayers+1):
            self.layers[:,j] = np.dot(self.weights[j], self.sigmoids[:,j-1]) + self.biases[:,j]
            self.sigmoids[:,j] = 1 / (1 + np.exp(-self.layers[:,j]))
        if not nox:
            self._error += self.sigmoids[:,self.nlayers] - o
        return self.sigmoids[:, self.nlayers]


    def back_propagate(self, ys):
        delta = self._error / len(ys)
        for i in range(self.nlayers, 0, -1):
            self.weights[i] -= self.lr * self.sigmoids[:,i-1] * delta
            self.biases[:,i] -= self.lr * delta
            delta = np.dot(self.weights[i].T, delta) * (self.sigmoids[:,i-1]*(1-self.sigmoids[:,i-1]))


    def learn(self, examples):
        for i, e in enumerate(examples):
            self.feed_forward(e)
            if (i+1)%self._batchsize==0:
                self.back_propagate([e[1] for e in examples[i+1-self._batchsize:i+1]])
                self._error = 0
        self._error = 0


    def predict(self, i):
        return self.feed_forward((i,0), nox=True)



if __name__=='__main__':
    N = FeedForwardNN(2,6,2)
    examples = [
                (np.array([1,0]),np.array([1,0])), (np.array([0,1]),np.array([0,1])),
                (np.array([2,0]),np.array([1,0])), (np.array([0,2]),np.array([0,1])),
                (np.array([3,0]),np.array([1,0])), (np.array([0,3]),np.array([0,1])),
                (np.array([4,0]),np.array([1,0])), (np.array([0,4]),np.array([0,1])),
                (np.array([5,0]),np.array([1,0])), (np.array([0,5]),np.array([0,1])),
                (np.array([6,0]),np.array([1,0])), (np.array([0,6]),np.array([0,1])),
                (np.array([7,0]),np.array([1,0])), (np.array([0,7]),np.array([0,1])),
                (np.array([8,0]),np.array([1,0])), (np.array([0,8]),np.array([0,1]))
                ]
    N.learn(examples)
    for w in N.weights:
        print(w)
