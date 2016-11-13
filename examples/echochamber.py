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
#       >> python echochamber.py
#
# For first use, set DEMO=False and GET_NEW_AXES=True

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from imgurpca import Query
from imgurpca import Parser
from imgurpca import Learner
from imgurpca.macros import gen_axes
from imgurpython.helpers.error import ImgurClientError
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import math
try:
    from myconfig import *
except ImportError:
    print('myconfig.my does not exist. Please create it with CS=client_secret and CID=client_id variables.')
    exit(-1)

AXES_FILE = 'axes_demo.csv'
NUM_AXES = 2
NUM_POINTS = 75
client_secret = CS
client_id = CID
DEMO = True
GET_NEW_AXES = False
learner = Learner()
past_choices = deque()      # indices to coords in chain

def get_common_words(fname):
    with open(fname, 'r') as f:
        words = f.readlines()
    words = [w.strip() for w in words]
    return words

def get_projections():
    learner.load_axes(AXES_FILE)
    learner.axes = learner.axes[:,0:NUM_AXES]
    if DEMO:
        return [c for c in np.random.randint(0,50, size=(NUM_POINTS, NUM_AXES))]
    else:
        q = Query(Query.RANDOM).construct()
        p = Parser(cs=client_secret, cid=client_id)
        p.get(q, pages=(0, math.ceil(NUM_POINTS/60)))
        p.items = p.items[:NUM_POINTS]

        projections = []
        for item in p.items:
            item.generate_word_counts()
            projections.append(learner.project(item))

def recommend(coords, choices):
    weighted_choices = [coords[c]/(n+1) for n,c in enumerate(reversed(choices))]
    centroid = np.sum(weighted_choices, axis=0) / NUM_AXES
    distances = [np.dot(c-centroid, c-centroid) for c in coords]
    r = np.argmax(distances)
    while r in choices:
        r = np.argmax(distances[:r] + distances[r+1:])
    return r

def visualize(coords, choices, r):
    plt.clf()
    labels = ['{0}'.format(i) for i in range(NUM_POINTS)]
    plt.subplots_adjust(bottom = 0.1)
    plt.scatter(
        [d[0] for d in coords], [d[1] for d in coords], marker = 'o',
        c = [100 if c in choices else 200 if c==r else 50 for c in range(NUM_POINTS)], s = 512,
        cmap = plt.get_cmap('Spectral'))
    for label, x, y in zip(labels, [d[0] for d in coords], [d[1] for d in coords]):
        plt.annotate(
            label,
            xy = (x, y), xytext = (11, -11),
            textcoords = 'offset points', ha = 'right', va = 'bottom',
            # bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
            # arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0')
            )
    plt.show(block=False)


if __name__=='__main__':
    words=get_common_words('./filter.txt')
    if not DEMO and GET_NEW_AXES:    # downloaded during development
        q = Query(Query.TAG).params('politics').sort_by(Query.TOP).over(Query.ALL).construct()
        gen_axes(output=AXES_FILE, p=(0,1), n=10, remove=words, cs=client_secret, cid=client_id, verbose=True, query=q)

    coords = get_projections()
    if len(coords)==0:
        exit(-1)

    for i in range(NUM_AXES):
        past_choices.append(i)
    c= 0
    while True:
        while c in past_choices:
            try:
                c = int(raw_input('Enter choice: '))
            except NameError:
                c = int(input('Enter choice: '))
        past_choices.popleft()
        past_choices.append(c)
        r = recommend(coords, past_choices)
        print('Choices: ' + str(past_choices))
        print('Recommendation: ' + str(r) + ';\tCoord: ' + str(coords[r]))

        if NUM_AXES==2:
            visualize(coords, past_choices, r)
