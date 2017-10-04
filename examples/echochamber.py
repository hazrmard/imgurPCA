# EchoChamber is a content recommendation system that encourages diverse thought.
# The algorithm proceeds as follows:
#
#     * parse textual content for training
#     * preprocess data (filter out common words etc.)
#     * Use Principal Component Analysis to reduce dimensionality of data points.
#     * Generate axes using Principal Components
#     * Parse/Preprocess textual content for testing
#     * Project testing data to axes
#     * Generate a Markv chain where the next state depends on maximizing a distance metric from previous choices
#     * For each choice, update Markov chain and provide recommendation
#
# Use requires installation of imgurpca (https://github.com/hazrmard/imgurPCA)
# Usage:
#       >> python examples/echochamber.py
#
# For first use, set DEMO=False and GET_NEW_AXES=True

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

# add one directory up to PATH so imgurpca doesn't need to be installed to
# run this script
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from collections import deque
import math
from argparse import ArgumentParser
import numpy as np
import matplotlib.pyplot as plt
import flask

from imgurpca import Query
from imgurpca import Parser
from imgurpca import Learner
from imgurpca.macros import gen_axes
from imgurpython.helpers.error import ImgurClientError

try:
    from myconfig import CS, CID
except ImportError:
    print('myconfig.my does not exist. Please create it with CS=client_secret and CID=client_id variables.')
    exit(-1)

# default arguments
AXES_FILE = 'axes.csv'
NUM_AXES = 2
NUM_POINTS = 75
client_secret = CS
client_id = CID
learner = Learner()
past_choices = deque()      # indices to coords in chain

# set up command-line interface
ARGS = ArgumentParser(description='Echochamber demo.')
ARGS.add_argument('-l', '--load', default=None, type=str, metavar='L.csv',
                  help='Name of .csv file to load axes from. By default generates axes to: ' + AXES_FILE)
ARGS.add_argument('-s', '--store', default=None, type=str, metavar='S.csv',
                  help='Name of .csv file to write axes to. Default:' + AXES_FILE)
ARGS.add_argument('-n', '--num-axes', default=NUM_AXES, type=int, metavar='N',
                  help='Number of axes to generate.')
ARGS.add_argument('-p', '--points', default=NUM_POINTS, type=int, metavar='P',
                  help='Number of posts to use to generate axes.')
ARGS.add_argument('-x', '--filter', default=None, type=str, metavar='X.txt',
                  help='Path to newline delimted file containing words to filter out.')


def get_common_words(fname):
    with open(fname, 'r') as f:
        words = f.readlines()
    words = [w.strip() for w in words]
    return words


def recommend(coords, choices):
    weighted_choices = [coords[c]/(n+1) for n,c in enumerate(reversed(choices))]
    centroid = np.sum(weighted_choices, axis=0) / NUM_AXES
    distances = [np.dot(c-centroid, c-centroid) for c in coords]
    r = np.argmax(distances)
    while r in choices:
        r = np.argmax(distances[:r] + distances[r+1:])
    return r


APP = flask.Flask(__name__)


if __name__ == '__main__':
    ARGS = ARGS.parse_args()
    
    if ARGS.file is not None:
        # load axes from file
        pass
    else:
        # generate new axes
        pass