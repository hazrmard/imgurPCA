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
from argparse import Action
import numpy as np
import matplotlib.pyplot as plt
import flask

from imgurpca import Query
from imgurpca import Parser
from imgurpca import Learner
from imgurpca.macros import gen_axes
from imgurpython.helpers.error import ImgurClientError


from myconfig import CS, CID, CS1, CID1

# default arguments
AXES_FILE = 'axes.csv'
NUM_AXES = 2
NUM_POINTS = 75
POSTS_PER_PAGE = 60
NUM_WORDS = 50
DEFAULT_QUERY = Query(Query.GALLERY_TOP).over(Query.WEEK).sort_by(Query.TOP).construct()
learner = Learner()
past_choices = deque()      # indices to coords in chain


class QueryParser(Action):
    """
    Parses query string passed by --query or -q option. Of the form:
        WHAT [FunctionName1:Argument] [FunctionName2:Argument] ....
    Where WHAT is the instantiation argument to Query() class.
    Where FunctionName is one of Query.[sort_by, over, params], and Argument
    is the argument passed to it. For example:
        gallery_top over:day sort_by:hot
    """
    def __call__(self, parser, namespace, values, option_string=None):
        query = Query(getattr(Query, values[0].upper()))
        for val in values[1:]:
            func, arg = val.split(':')
            getattr(query, func.lower())(arg)
        setattr(namespace, 'query', query.construct())



# set up command-line interface
ARGS = ArgumentParser(description='Echochamber demo.')
ARGS.add_argument('-l', '--load', default=None, type=str, metavar='L.csv',
                  help='Name of .csv file to load axes from. By default generates axes to: ' + AXES_FILE)
ARGS.add_argument('-s', '--save', default=None, type=str, metavar='S.csv',
                  help='Name of .csv file to write axes to. Default:' + AXES_FILE)
ARGS.add_argument('-n', '--num-axes', default=NUM_AXES, type=int, metavar='N',
                  help='Number of axes to generate.')
ARGS.add_argument('-p', '--points', default=NUM_POINTS, type=int, metavar='P',
                  help='Number of posts to use to generate axes.')
ARGS.add_argument('-w', '--words', default=NUM_WORDS, type=int, metavar='W',
                  help='Number of top most frequent words to use to generate axes.')
ARGS.add_argument('-q', '--query', default=DEFAULT_QUERY, type=str, metavar='Q', nargs='+',
                  action=QueryParser, help='Query parameters: <WHAT> [Func1:Arg] ...')
ARGS.add_argument('-f', '--filter', default=None, type=str, metavar='F.txt',
                  help='Path to newline delimted file containing words to filter out.')


def get_common_words(fname):
    """
    reads a newline delimited file for words to ignore in analysis.
    """
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
    A = ARGS.parse_args()
    P = Parser(cid=CID, cs=CS)
    L = Learner()
    
    if A.load is not None:
        L.load_axes(A.load)
    else:
        filter_words = get_common_words(A.filter)
        gen_axes(output=A.save, remove=filter_words, n=A.points,
                      pages=(0, A.points // POSTS_PER_PAGE + 1), topn=A.words,
                      verbose=True, query=A.query, cs=CS1, cid=CID1)
        L.load_axes(A.save)