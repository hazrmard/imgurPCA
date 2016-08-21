from imgurpython import ImgurClient
import utils
import config
import numpy as np

class Post(object):

    def __init__(self, id, **kwargs):
        self.id = id                    # str
        self.user = None                # account object (see imgur API doc.)
        self.comments = []              # array of comment objects (see imgur API doc.)
        self.wordcount = np.array([], dtype=config.DT_WORD_WEIGHT)
        self.word_weight = config.DEFAULT_WORD_WEIGHT

        if 'cid' in kwargs and 'cs' in kwargs:
            self.client = ImgurClient(kwargs['cid'], kwargs['cs'])
        elif 'client' in kwargs:
            self.client = kwargs['client']
        else:
            raise config.InvalidArgument('Either include client=ImgurClient()'
                                ' instance, or cid=CLIENT_ID and cs=CLIENT_SECRET')

        for attr in kwargs:
            setattr(self, attr, kwargs[attr])


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


    def set_word_weight_func(func):
        """word weight=>f(post score, comment votes, comment level)
        Top level comments = 1, 2nd level from top = 2,...
        Default word weighting = word frequency in comments
        """
        self.word_weight = func


    def generate_word_counts(self, child_comments=False, comment_votes=True,
                            comment_level=True):
        words = {}
        if child_comments:
            iterable = utils.flatten(self.comments)
        else:
            iterable = zip(self.comments, [1]*len(self.comments))

        for c in iterable:      # c => (comment, nest level)
            vote = c[0].points if comment_votes else 1
            level = c[1] if comment_level else 1
            weight = self.word_weight(self.points, vote, level)
            for w in utils.sanitize(c[0].comment):
                try:
                    words[w] += weight
                except KeyError:
                    words[w] = weight

        unique, counts = np.unique(words.keys(), return_counts=True)
        self.wordcount = np.array([(w, words[w]*counts[i]) for i,w in
                                enumerate(words)], dtype=config.DT_WORD_WEIGHT)
