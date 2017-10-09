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
# absolute path of repository
ABSPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# absolute path to the template and static files folder
TEMPLATEDIR = os.path.join(ABSPATH, 'examples')
STATICDIR = TEMPLATEDIR
# name of template file relative to TEMPLATEDIR
TEMPLATEFILE = 'echochamber.html'
# path of pickled posts file
PICKLEFILE = os.path.join(STATICDIR, 'posts.pickle')
sys.path.append(ABSPATH)

from collections import deque
import math
import pickle
from argparse import ArgumentParser
from argparse import Action
import numpy as np
import matplotlib.pyplot as plt
import flask

from imgurpca import Query
from imgurpca import Parser
from imgurpca import Learner
from imgurpca.imutils import QueryParser, get_credits
from imgurpca.macros import gen_axes
from imgurpython.helpers.error import ImgurClientError


from myconfig import CS, CID

# default arguments
AXES_FILE = 'axes.csv'
NUM_AXES = 2
NUM_POINTS = 75
NUM_POSTS = 5
POSTS_PER_PAGE = 60
NUM_WORDS = 50
DEFAULT_QUERY = Query(Query.GALLERY_TOP).over(Query.WEEK).sort_by(Query.TOP).construct()
DEFAULT_REQUEST = Query(Query.GALLERY_HOT).sort_by(Query.VIRAL).construct()
learner = Learner()
past_choices = deque()      # indices to coords in chain



# set up command-line interface
ARGS = ArgumentParser(description='Echochamber demo.')
ARGS.add_argument('-l', '--load', default=None, type=str, metavar='L.csv',
                  help='Name of .csv file to load axes from. By default generates axes to: ' + AXES_FILE)
ARGS.add_argument('-s', '--save', default=None, type=str, metavar='S.csv',
                  help='Name of .csv file to write axes to. Default:' + AXES_FILE)
ARGS.add_argument('-a', '--axes', default=NUM_AXES, type=int, metavar='N',
                  help='Number of axes to generate.')
ARGS.add_argument('-p', '--points', default=NUM_POINTS, type=int, metavar='P',
                  help='Number of posts to use to generate axes.')
ARGS.add_argument('-m', '--posts', default=NUM_POSTS, type=int, metavar='M',
                  help='Number of posts to project onto axes from request query.')
ARGS.add_argument('-w', '--words', default=NUM_WORDS, type=int, metavar='W',
                  help='Number of top most frequent words to use to generate axes.')
ARGS.add_argument('-q', '--query', default=DEFAULT_QUERY, type=str, metavar='Q', nargs='+',
                  action=QueryParser, help='Query parameters: <WHAT> [Func1:Arg] ...')
ARGS.add_argument('-r', '--request', default=DEFAULT_REQUEST, type=str, metavar='R', nargs='+',
                  action=QueryParser, help='Query parameters: <WHAT> [Func1:Arg] ...')
ARGS.add_argument('-f', '--filter', default=None, type=str, metavar='F.txt',
                  help='Path to newline delimted file containing words to filter out.')
ARGS.add_argument('-x', '--demo', default=False, action='store_true',
                  help='Demo flag. If specified, loads pre-downloaded posts to project.')


def get_common_words(fname):
    """
    reads a newline delimited file for words to ignore in analysis.
    """
    with open(fname, 'r') as f:
        words = f.readlines()
    words = [w.strip() for w in words]
    return words


def recommend(coords, choices):
    """
    A redcommendation algorithm that takes previous choices from coords and
    recommends the next choice in coord.
    """
    weighted_choices = [coords[c]/(n+1) for n,c in enumerate(reversed(choices))]
    centroid = np.sum(weighted_choices, axis=0) / NUM_AXES
    distances = [np.dot(c-centroid, c-centroid) for c in coords]
    r = np.argmax(distances)
    while r in choices:
        r = np.argmax(distances[:r] + distances[r+1:])
    return r



if __name__ == '__main__':
    C = deque()                     # Choices: history of user choices
    A = ARGS.parse_args()           # Arguments parsed from command line
    Q = A.request                   # Query for requesting posts to project
    P = Parser(cid=CID, cs=CS)      # Parser instance
    L = Learner()                   # Learner instance
    X = []                          # List of projection coordinates
    F = get_common_words(A.filter)  # Filter: List of words to filter out.

    credits = get_credits(P.client)
    [print(x[0]+': '+str(x[1]),end='\n') for x in credits.items()]
    if credits['UserRemaining']==0 and (A.load is None or not A.demo):
        print('Usage limit exceeded. Retry after %s.' % credits['UserReset'])
        exit(-1)
    
    # Load or generate axes
    if A.load is not None:
        L.load_axes(A.load)
    else:  
        gen_axes(output=A.save, remove=F, n=A.points,
                 pages=(0, A.points // POSTS_PER_PAGE + 1), topn=A.words,
                 verbose=True, query=A.query, axes=A.axes, cs=CS, cid=CID)
        L.load_axes(A.save)
    
    # Get initial posts to plot, and consolidate wordcounts
    if A.demo:
        print('Demo. Loading previously saved posts from %s' % PICKLEFILE)
        with open(PICKLEFILE, 'rb') as f:
            P.items = pickle.load(f)
    else:
        print('Getting: ', Q)
        P.get(Q, pages=(0, A.posts // POSTS_PER_PAGE + 1))
        P.items = P.items[:A.posts]
        print('Downloading: %d' % len(P.items))
        P.download()
        print('Saving downloads to file for demo purposes: %s' % PICKLEFILE)
        with open(PICKLEFILE, 'wb') as f:
            pickle.dump(P.items, f)
    for post in P.items:
        post.generate_word_counts()
    P.consolidate(words=F, reverse=True)


    # Get initial projections
    X = L.project(P)
    
    APP = flask.Flask(__name__, static_url_path='',
                      static_folder=STATICDIR,
                      template_folder=TEMPLATEDIR)
    
    @APP.route('/')
    def index():
        """
        Renders the page.
        """
        return flask.render_template(TEMPLATEFILE, CS=CS, CID=CID)


    @APP.route('/axes/', methods=['POST'])
    def axes(): pass


    @APP.route('/query/')
    def query(): pass


    @APP.route('/choice/', methods=['POST'])
    def choice(): pass


    @APP.route('/recommend/')
    def recommend(): pass

    @APP.route('/update/')
    def update():
        return flask.jsonify(points=[list(x) for x in X])


    APP.run(debug=1)