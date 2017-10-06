from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from .. import Query
from .. import Parser
from .. import Learner
from .. import imutils
import numpy as np
import sys


def gen_axes(cs, cid, output=None, remove=[], pages=(0,3), n=150, topn=50, verbose=False, query=None):
    """generate axes from comments on gallery random section, first 2 pages, top
    n posts, sorted by top, over 1 week. axes are generated from the top 25
    words with the largest variance / mean ratio.
    @param cid (string): client id, use with 'cs'
    @param cs (string): client secret, use with 'cid'.
    @param n (int): # of posts
    @param pages (int/tuple): page number / range of pages to download
    @param topn (int): # of words to use in axes generation
    @param query (Query): Query instance with construct() called
    @param remove (list): collection of words to filter out
    """
    p = Parser(cs=cs, cid=cid)        # set up parser with client
    q = Query(Query.RANDOM).construct() if query is None else query
    if __name__=='__main__' or verbose:
        print('Downloading posts for: ', q)
    p.get(q, pages=pages)           # get post ids + metadata based on query
    if __name__=='__main__' or verbose:
        print('Downloaded %d posts over %s pages' % (len(p.items), pages))
    p.items = p.items[:n]
    p.download()                # download post comments

    if __name__=='__main__' or verbose:
        print('Processing ' + str(len(p.items)) + ' posts ...')

    for post in p.items:        # get word counts for each post
        post.generate_word_counts()
        post.filter_by_word(remove, reverse=True)

    p.items = [post for post in p.items if len(post.wordcount)]  # in case rate limit prevents comment download
    if len(p.items)==0:
        print('No posts could be downloaded.')
        exit(-1)


    p.consolidate()             # make words uniform across posts
    m, v = p.get_baseline()     # get means and variances for words
    top = np.argsort(v/m)[::-1]   # indices for variance in descending order
    p.consolidate(words=p.words[top[:topn]])  # only leave top 25 words by variance

    l = Learner(source=p)
    ax = l.get_axes()

    if output is not None:      # store axes if filename specified
        l.save_axes(fname=output)
    if __name__!='__main__':    # do not return array if running as a script
        return ax
    if __name__=='__main__' or verbose:
        print('Finished.')


if __name__=='__main__':
    if len(sys.argv)!=4 or '-h' in sys.argv:        # no arguments provided
        print('\nUsage:\tpython -m imgurpca.macros.gen_axes CLIENT_SECRET CLIENT_ID',
                'OUTPUT_FILE\n')
        exit(0)
    gen_axes(output=sys.argv[3], cs=sys.argv[1], cid=sys.argv[2])
