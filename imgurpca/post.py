from __future__ import unicode_literals
from __future__ import absolute_import
from . import utils
from . import config
from . import imutils
from .base import Atomic
import numpy as np

# The Post class represents a single gallery item on imgur.com. Each post is
# identified by its 'id'. Post methods provide a way to download, cleanse, and
# filter data into word counts. Post instances are used by the Parser class to
# conduct comulative operations on Posts satifying some query.

class Post(Atomic):

    def __init__(self, id, **kwargs):
        """
        @param id (str): post id
        @param cid (string): client id, use with 'cs'
        @param cs (string): client secret, use with 'cid'.
        OR:
        @param client (ImgurClient): imgurpython.ImgurClient instance
        All other attributes are optional and are set by class methods or can
        be provided as key value arguments.
        """
        self.id = id                    # str
        self.user = None                # account object (see imgur API data model.)
        self.comments = []              # array of comment objects (see imgur API doc.)

        imutils.set_up_client(self, **kwargs)
        super(Post, self).__init__(**kwargs)

    @property                           # list of users associated with post
    def network(self):
        return self.get_user_ids()

    @property                           # reference to data source for wordcount
    def content(self):
        return self.comments


    def download(self):
        """download the relevant gallery post, comments, and user data based on
        self.id.
        """
        post_obj = self.client.gallery_item(self.id)
        for attr in post_obj.__dict__:
            setattr(self, attr, post_obj.__dict__[attr])

        if post_obj.account_url:
            self.user = self.client.get_account(post_obj.account_url)

        self.comments = self.client.gallery_item_comments(self.id)


    def get_user_ids(self, replies=False):
        """return a list of usernames (url) that commented on post.
        @param replies (boolean): True-> include child comments
        """
        if replies:
            iterable = utils.flatten(self.comments)
        else:
            iterable = zip(self.comments, [1]*len(self.comments))
        return [c[0].author for c in iterable]


    def set_word_weight_func(self, func):
        """word weight=>f(post score, comment votes, comment level)
        Top level comments = 1, 2nd level from top = 2,...
        Default word weighting = word frequency in comments
        """
        self.word_weight = func


    def generate_word_counts(self, child_comments=False, comment_votes=True,
                            comment_level=True):
        """generate a numpy array of words and their weights as determined by
        self.word_weight function.
        @param child_comments (bool): whether to parse child comments or not
        @param comment_votes (bool): whether to pass comment votes to self.word_weight,
                                    False passes 1 for all comments.
        @param comment_level (bool): whether to pass comment nest level to
                                    self.word_weight, False passes 1 for all comments.
        """
        words = {}
        if child_comments:
            iterable = utils.flatten(self.content)
        else:
            iterable = zip(self.content, [1]*len(self.content))

        for c in iterable:      # c => (comment, nest level)
            vote = c[0].points if comment_votes else 1
            level = c[1] if comment_level else 1
            weight = self.word_weight(self.points, vote, level)
            for w in utils.sanitize(c[0].comment):
                try:
                    words[w] += weight
                except KeyError:
                    words[w] = weight

        self.wordcount = np.array(list(words.items()), dtype=config.DT_WORD_WEIGHT)
