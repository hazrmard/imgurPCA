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
#       >> python examples/echochamber.py -h
#       >> python .\examples\echochamber.py -s .\examples\politics.csv -a 2
#          -p 100 -w 75 -q tag sort_by:top over:all params:politics -f
#          .\examples\filter.txt --axes-only
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

import math
import pickle
from argparse import ArgumentParser
from argparse import Action
import numpy as np
import matplotlib.pyplot as plt
import flask
import requests

from imgurpca import Query
from imgurpca import Parser
from imgurpca import Learner
from imgurpca import config
from imgurpca.imutils import parse_query_to_instance, QueryParser, get_credits
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



# set up command-line interface
ARGS = ArgumentParser(description='Echochamber demo.')
ARGS.add_argument('-l', '--load', default=None, type=str, metavar='L.csv',
                  help='Name of .csv file to load axes from. By default generates axes to: ' + AXES_FILE)
ARGS.add_argument('-s', '--save', default=None, type=str, metavar='S.csv',
                  help='Name of .csv file to write axes to. Default:' + AXES_FILE)
ARGS.add_argument('-a', '--axes', default=NUM_AXES, type=int, metavar='A',
                  help='Number of axes to generate.')
ARGS.add_argument('-p', '--points', default=NUM_POINTS, type=int, metavar='P',
                  help='Number of posts to use to generate axes.')
ARGS.add_argument('-m', '--posts', default=NUM_POSTS, type=int, metavar='M',
                  help='Number of posts to project onto axes from request query.')
ARGS.add_argument('-w', '--words', default=NUM_WORDS, type=int, metavar='W',
                  help='Number of top most frequent words to use to generate axes.')
ARGS.add_argument('-q', '--query', default=DEFAULT_QUERY, type=str, metavar='Q', nargs='+',
                  action=QueryParser, help='Query parameters for axes generation: <WHAT> [Func1:Arg] ...')
ARGS.add_argument('-r', '--request', default=DEFAULT_REQUEST, type=str, metavar='R', nargs='+',
                  action=QueryParser, help='Query parameters for projecting posts: <WHAT> [Func1:Arg] ...')
ARGS.add_argument('-f', '--filter', default=None, type=str, metavar='F.txt',
                  help='Path to newline delimted file containing words to filter out.')
ARGS.add_argument('-d', '--demo', default=False, action='store_true',
                  help='Demo flag. Loads cached posts to project. Default: False')
ARGS.add_argument('-c', '--cache', default=PICKLEFILE, nargs=1, type=str, metavar='C.pickle',
                  help='Cached posts file to save/load for demo. Default: ' + PICKLEFILE)
ARGS.add_argument('--axes-only', default=False, action='store_true',
                  help='If specified, exits after generating new axes.')


def get_common_words(fname):
    """
    reads a newline delimited file for words to ignore in analysis.
    """
    if fname is None:
        return []
    with open(fname, 'r') as f:
        words = f.readlines()
    words = [w.strip() for w in words]
    return words


def recommend(coords, choices):
    """
    A redcommendation algorithm that takes previous choices from coords and
    recommends the next choice in coord.
    Args:
        choices (list/array): Indices into coords representing choice history.
        coords (array): Coordinates/projections of posts on axes.
    Returns:
        An array representing suitability of coordinates as next choice.
        Ranges from [0, 1]
    """
    centroid = np.average(coords[choices], axis=0, weights=np.arange(1, len(choices)+1))
    deltas = coords - centroid              # vectors from centroid
    mag = np.linalg.norm(deltas, axis=1)    # vector magnitudes
    mag[choices] = 0                        # ignoring prior choices' distances to get [0-1] scale
    m = np.max(mag)                         # normalization factor
    m = 1 if m==0 else m                    # division by 0 edge case                   
    # magn = np.arccos(mag / m) / (np.pi / 2)
    magn = mag / m
    return magn



A = ARGS.parse_args()           # Arguments parsed from command line
setattr(A, 'proj', np.array([]))# set A.proj as reference to projections of posts
setattr(A, 'choices', [])       # set A.choices as reference to history
setattr(A, 'rec', np.array([])) # set A.rec as array of recommendation values
P = Parser(cid=CID, cs=CS)      # Parser instance
L = Learner()                   # Learner instance
F = get_common_words(A.filter)  # Filter: List of words to filter out.
ORIGINAL_AX = []                # stores originally loaded axes for resetting

credits = get_credits(P.client)
[print(x[0]+': '+str(x[1]),end='\n') for x in credits.items()]
if credits['UserRemaining']==0 and (A.load is None or not A.demo):
    print('Usage limit exceeded & no local axes specified. Retry after %s.' % credits['UserReset'])
    exit(-1)

# Load or generate axes
if A.load is not None:
    L.load_axes(A.load)
    L.axes = L.axes[:, :A.axes]
else:  
    gen_axes(output=A.save, remove=F, n=A.points,
                pages=(0, A.points // POSTS_PER_PAGE + 1), topn=A.words,
                verbose=True, query=A.query, axes=A.axes, cs=CS, cid=CID)
    L.load_axes(A.save)

# exit after generating axes if axes-only flag is specified
if A.axes_only:
    exit(0)

# storing axes as strings compatible w/ axes() in case client needs to reset
for i in range(A.axes):
    axis = zip(L.words, L.axes[:, i])           # iterable (word, weight)
    axis = [':'.join((t[0], str(t[1]))) for t in axis]  # list [(word:weight), ...]
    axis = ' '.join(axis)                       # string 'word:weight word:weight'
    ORIGINAL_AX.append(axis)


# Get initial posts to plot, and consolidate wordcounts
if A.demo:
    print('Demo. Loading previously saved posts from %s' % A.cache)
    with open(A.cache, 'rb') as f:
        P.items = pickle.load(f)
else:
    print('Getting: ', A.request)
    P.get(A.request, pages=(0, A.posts // POSTS_PER_PAGE + 1))
    P.items = P.items[:A.posts]
    print('Downloading: %d' % len(P.items))
    P.download()
    print('Saving downloads to file for demo purposes: %s' % A.cache)
    with open(A.cache, 'wb') as f:
        pickle.dump(P.items, f)
for post in P.items:
    post.generate_word_counts()
    post.normalize()
P.consolidate(words=F, reverse=True)
A.proj = L.project(P)

APP = flask.Flask(__name__, static_url_path='',
                    static_folder=STATICDIR,
                    template_folder=TEMPLATEDIR)

@APP.route('/')
def index():
    """
    Renders the page. Resets choice history.
    """
    A.choices = []
    A.rec = np.array([])
    return flask.render_template(TEMPLATEFILE, CS=CS, CID=CID)

@APP.route('/update/')
def update():
    """
    Returns a JSON object containing coords, weights, recommendations, axes
    limits, point URLS and any other information. Handled by the update()
    function in the client.
    """
    prefix = 'https://imgur.com/gallery/'
    return flask.jsonify(points=[list(x) for x in A.proj],
                            urls=[prefix+p.id for p in P.items],
                            weights=[len(p.comments) for p in P.items],
                            axesmin=list(np.min(A.proj, axis=0)[:A.axes]),
                            axesmax=list(np.max(A.proj, axis=0)[:A.axes]),
                            rec=list(A.rec)
                        )

@APP.route('/axes/')
def axes():
    """
    Sets new axes. Constrained to 2 axes (x and y) at the front end. The server
    side can handle any number of axes specified by --axes option. In case
    request is made with x or y axes missing, originals are restored.
    Posts are reprojected each time.
    """
    ax = []
    A.choices = []
    ax.append(flask.request.args.get('xaxis', default=ORIGINAL_AX[0]))
    ax.append(flask.request.args.get('yaxis', default=ORIGINAL_AX[1]))
    formatted_axes = []
    for i, axis in enumerate(ax):
        if len(axis) == 0:
            formatted_axes.append(np.array(list(zip(L.words, L.axes[:, i])),
                                            dtype=config.DT_WORD_WEIGHT))
        else:
            tokens = [tuple(t.split(':')) for t in axis.split()]
            formatted_axes.append(np.array(tokens, dtype=config.DT_WORD_WEIGHT))
    L.set_axes(formatted_axes, consolidated=False)
    A.proj = L.project(P)
    if len(A.choices):
        A.rec = recommend(A.proj, A.choices)
    return update()


@APP.route('/query/')
def query():
    """
    Obtains new posts from imgur based on the passed query.
    """
    A.choices = []
    qtext = flask.request.args.get('q', default='')
    posts = flask.request.args.get('n', default=A.posts, type=int)
    A.posts = posts
    if len(qtext) > 0:
        tokens = qtext.split()
        A.request = parse_query_to_instance(tokens).construct()
    P.get(A.request, pages=(0, A.posts // POSTS_PER_PAGE + 1))
    P.items = P.items[:A.posts]
    P.download()
    for post in P.items:
        post.generate_word_counts()
        post.normalize()
    P.consolidate(words=F, reverse=True)
    A.proj = L.project(P)
    return update()


@APP.route('/get/')
def get():
    """
    Downloads and passes on the raw HTML content of imgur pages to client
    since iframe cannot directly show cross-domain content. imgur loads comments
    dynamically - so X-domain prevents them showing. Start chrome instead with
    security features disabled to see comments.
    """
    url = flask.request.args.get('url')
    return requests.get(url).text



@APP.route('/choice/')
def choice():
    """
    Adds choice to history and generates new recommendations.
    """
    cindex = flask.request.args.get('c', type=int)
    A.choices.append(cindex)
    A.rec = recommend(A.proj, A.choices)
    return update()


@APP.route('/words/')
def words():
    """
    returns an array of objects of the form [{word:weight}...] ordered
    by descending weight. Used to make word cloud by client.
    Returns a JSON with 2 fields:
        - domain: containing min and max values for word sizes,
        - words: an array of objects with text & size fields 
    """
    num = flask.request.args.get('n', default=50, type=int)
    bins = flask.request.args.get('n', default=20, type=int)
    warr = np.sort(P.wordcount, order='weight')[-num:]
    warr['weight'] = np.sqrt(warr['weight'])
    mi = np.min(warr['weight'])
    ma = np.max(warr['weight'])
    step = (ma - mi) / bins
    warr['weight'] = np.digitize(warr['weight'], np.arange(mi, ma, step))
    return flask.jsonify(words=[{'text':w[0], 'size':w[1]} for w in warr],
                         domain=[mi, ma])


APP.run(debug=1)
