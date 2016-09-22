from __future__ import absolute_import
from __future__ import print_function
from imgurpca import Query
from imgurpca import Parser
from imgurpca import Learner
from imgurpca import imutils
import numpy as np
import sys


def gen_axes(output=None, **kwargs):
    """generate axes from comments on gallery top section, first page, sorted
    by top, over 1 week. axes are generated from the top 25 most varying words in
    the gallery posts.
    @param cid (string): client id, use with 'cs'
    @param cs (string): client secret, use with 'cid'.
    OR:
    @param client (ImgurClient): imgurpython.ImgurClient instance
    """
    p = Parser(**kwargs)        # set up parser with client
    q = Query(Query.GALLERY_TOP).sort_by(Query.TOP).over(Query.WEEK).construct()
    if __name__=='__main__':
        print('Downloading posts...')
    p.get(q, pages=0)           # get post ids + metadata based on query
    p.download()                # download post comments

    if __name__=='__main__':
        print('Processing ' + str(len(p.items)) + ' posts ...')

    for post in p.items:        # get word counts for each post
        post.generate_word_counts()

    p.items = [x for x in p.items if len(x.wordcount)]  # in case rate limit prevents comment download
    if len(p.items)==0:
        print('No posts could be downloaded due to Rate Limits. Try later.')
        exit(1)

    p.consolidate()             # make words uniform across posts
    m, v = p.get_baseline()     # get means and variances for words
    top = np.argsort(v)[::-1]   # indices for variance in descending order
    p.consolidate(words=p.words[top[:25]])  # only leave top 25 words by variance

    l = Learner(source=p)
    ax = l.get_axes()
    
    if output is not None:      # store axes if filename specified
        l.save_axes(fname=output)
    if __name__!='__main__':    # do not return array if running as a script
        return ax
    if __name__=='__main__':
        print('Finished.')


if __name__=='__main__':
    if len(sys.argv)!=4 or '-h' in sys.argv:        # no arguments provided
        print('\nUsage:\tpython -m imgurpca.base.gen_axes CLIENT_SECRET CLIENT_ID',
                'OUTPUT_FILE\n')
        exit(0)
    gen_axes(output=sys.argv[3], cs=sys.argv[1], cid=sys.argv[2])
