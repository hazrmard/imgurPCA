# obfuscate.py is an example script that uses imgurpca classes.
# This script tries to distort information that can be obtained from a user's
# commenting activity by posting random comments on random posts.
# The script can be used by first prividing values for the CLIENT_ID and
# CLIENT_SECRET variables, and then calling:
#
# >> python obfuscate.py LOCATION_OF_CREDENTIAL_FILE
#
# Where LOCATION_OF_CREDENTIAL_FILE is the path to an existing *.cred file
# containing credentials obtained by calling Bot.authorize(). In case no such
# file exists, and the filepath is still provided, the script will prompt for
# authentication and store credentials in that file location for future use.
#
# Due to commenting rate restrictions, the script waits for an interval between
# comments. This means that it takes a while for it to finish running.
#
# The robustness of this script can be improved by:
#   * variable/random intervals between comments.
#   * posting comment replies (not just top level comments)
#   * posting upvotes/downvotes sporadically
#   * uploading posts to imgur
#
# All of these features can be added using functions in the Bot class.

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from imgurpca import Bot
from imgurpca import Query
from imgurpca import Parser
from imgurpca.macros import Chatter
import os
import sys
import time
from imgurpython.helpers.error import ImgurClientError


CLIENT_ID = ''
CLIENT_SECRET = ''

def obfuscate(credfile):

    b = Bot(cs=CLIENT_SECRET, cid=CLIENT_ID)        # instantiate a Bot to act on user's behalf

    if not os.path.exists(credfile) or credfile is None:
        print('Please go to this URL to obtain an authorization pin:')
        print(b.auth_url)
        try:                                            # obtain credentials
            pin = raw_input('Enter authorization pin: ')
        except NameError:                               # python 2/3 have different input functions
            pin = input('Enter authorization pin: ')
            b.authorize(pin, credfile)                  # log the Bot in, store credentials for next time
    else:
        b.load_credentials(credfile)                    # or get credentials from file



    print('Downloading and parsing content...')
    p = Parser(client=b.client)                     # instantiate parser
    q = Query(Query.RANDOM).construct()             # construct query for random gallery posts
    p.get(q, pages=0)                               # obtain 1 page of 60 posts
    p.download()                                    # download post comments

    c = Chatter(source=p, order=3)                  # create Chatter with p as source
    c.generate_chain()                              # create markov chain of order 3

    print('Posting comments...')
    ids = [post.id for post in p.items]
    b.every(Bot.SECOND*30).do(post_comment).using((b,c,ids)).times(len(ids)).go()  # start automated comment posting


def post_comment(bot, chatter, ids):                        # provided to Bot.do()
    try:
        pid = ids.pop()                                     # get a post id
    except IndexError:
        return

    while True:
        try:
            bot.post_comment(pid, chatter.random_comment())    # post a random comment
            break                                              # leave loop after comment
        except ImgurClientError:
            print('\rError encountered. Retrying in 30 seconds...', end='') # print status
            time.sleep(30)                                  # repeat in case of error (likely rate limit)
    print('\r' + ' '*50, end='')                            # clear line
    print('\r' + str(len(ids)) + ' comments left.', end='') # print status



if __name__=='__main__':

    credfile = sys.argv[1] if len(sys.argv)>1 else ''
    obfuscate(credfile)
