from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from imgurpython import ImgurClient
from imgurpython.imgur.models.image import Image
from imgurpython.imgur.models.album import Album
from imgurpython.imgur.models.gallery_album import GalleryAlbum
from imgurpython.imgur.models.account import Account
from imgurpython.helpers.error import ImgurClientRateLimitError, ImgurClientError
from imgurpca.post import Post
from imgurpca.user import User
from imgurpca.query import Query
from imgurpca.parallel import Parallel
import imgurpca.utils as utils
import imgurpca.config as config
import numpy as np

# The Parser class performs operations on a collection of Post or User objects
# stored in Parser.items. Parser can either populate posts from IDs or from a
# Query object. In addition it performs feature selection operations on the
# downloaded data.

class Parser(object):

    class Downloader(Parallel):
        def parallel_process(self, pkg, common):
            pkg.download()


    def __init__(self, nthreads=8, *args, **kwargs):
        """
        @param nthreads (int): number of threads to run content downloads on.
        @param cid (string): client id, use with 'cs'
        @param cs (string): client secret, use with 'cid'.
        OR:
        @param client (ImgurClient): imgurpython.ImgurClient instance
        """
        utils.set_up_client(self, **kwargs)
        self.items = []
        self.nthreads = nthreads
        self.wordcount = None
        self._consolidated = False      # flag to signal if all wordcounts sorted
        for attr in kwargs:
            setattr(self, attr, kwargs[attr])

        self._query_to_client = {Query.GALLERY_TOP: self.client.gallery,
                                Query.GALLERY_HOT: self.client.gallery,
                                Query.GALLERY_USER: self.client.gallery,
                                Query.SUBREDDIT: self.client.subreddit_gallery,
                                Query.TAG: self.client.gallery_tag,
                                Query.CUSTOM: self.client.gallery_search,
                                Query.RANDOM: self.client.gallery_random,
                                Query.MEMES: self.client.memes_subgallery}

    @property
    def comments(self, flatten=True):
        """returns a generaor containing lists of comment objects for all items.
        [[post1.comments], [post2.comments]...[postn.comments]]
        See imgur API data models for comment object attributes.
        """
        for item in self.items:
            if flatten:
                for comment, level in utils.flatten(item.comments):
                    yield comment
            else:
                for comment in item.comments:
                    yield comment

    @property
    def words(self):
        return self.wordcount['word']

    def download(self):
        """downloads whatever items (User/Post objects) are placed in self.items
        """
        D = Parser.Downloader(self.items, nthreads=self.nthreads)
        try:
            D.start()
            D.wait_for_threads()
        except ImgurClientRateLimitError:
            print('Rate limit exceeded:\n' + str(self.client.credits))


    def get_posts(self, query, pages=0):
        """instantiates posts to self.items.
        @param query (Query): a Query instance. See query.py.
        @param pages (int/tuple): page number or range of pages (inclusive) to get
        """
        source_func = self._query_to_client[query.mode]
        self.items = []
        if isinstance(pages, int):
            self.items.extend(source_func(page=pages, **query.content))
        elif isinstance(pages, (tuple,list)):
            for i in range(*pages):
                self.items.extend(source_func(page=i, **query.content))
        self.items = [Post(client=self.client, **p.__dict__) for p in self.items]


    def populate_posts(self, posts):
        """instantiate Post objects to self.items given post ids
        @param posts (list): a collection of post ids to download
                        OR a collection of imgurpython Image/Album class objects
        """
        if isinstance(posts[0], (Image, Album, GalleryAlbum)):
            self.items = [Post(client=self.client, **p.__dict__) for p in posts]
        else:
            self.items = [Post(client=self.client, id=p) for p in posts]


    def populate_users(self, users):
        """instantiate User objects to self.items, given post ids
        @param users (list): a collection of user ids (usernames) to download
                        OR a collection of imgurpython Account class objects
        """
        if isinstance(users[0], Account):
            self.items = [User(client=self.client, **u.__dict__) for u in users]
        else:
            self.items = [User(client=self.client, url=u) for u in users]


    def consolidate(self, words=None):
        """Generate a cumulative wordcount from the items' wordcounts. Add 0-weight
        words to items' wordlists so all items have the same set of words. Sort
        cumulative wordlist and item wordlists (by word) so index positions are
        identical.
        @param words (list/array): OPTIONAL - a list of words to keep and consolidate.
                                Otherwise, generates list of unique words from
                                all wordcounts in self.items
        """
        if len(self.items)==0:
            raise config.PrematureFunctionCall('No User/Post objects in self.items.')
        word_dict = {}
        if words is not None:           # initialize dict with acceptable words
            word_dict = {w:0 for w in words}

        for item in self.items:
            if item.wordcount is None:
                raise config.PrematureFunctionCall('Generate wordcounts first.')
            for w in item.wordcount:
                try:
                    word_dict[w['word']] += w['weight']
                except KeyError:
                    if words is None:   # otherwise skip word not in words
                        word_dict[w['word']] = w['weight']
        self.wordcount = np.array(word_dict.items(), dtype=config.DT_WORD_WEIGHT)
        self.wordcount.sort(order=[config.DEFAULT_SORT_ORDER])

        for item in self.items:
            zero_words = np.setdiff1d(self.wordcount['word'], item.wordcount['word'], assume_unique=True)
            zero_wordcounts = np.array(zip(zero_words, np.zeros(len(zero_words))), dtype=config.DT_WORD_WEIGHT)
            item.wordcount = np.append(item.wordcount, zero_wordcounts)
            item.sort()     # using default sort order
        self._consolidated = True


    def get_baseline(self):
        """given the wordcounts for all self.items, find the average weight
        and variance of each word. This can then be used to filter out frequent
        or consistently appearing words to reduce bloat. Can only be called after
        consolidation.
        Returns a tuple -> (average scores, variances) of 1D np arrays where
        order corresponds to self.words.
        """
        if not self._consolidated:
            raise config.PrematureFunctionCall('Consolidate Parser first.')
        matrix = np.zeros((len(self.items), len(self.words)))
        for i, item in enumerate(self.items):
            matrix[i,:] = item.wordcount['weight']
        means = np.mean(matrix, axis=0)
        variances = np.var(matrix, axis=0)
        return (means, variances)


    def split(self, fraction=0.5):
        """split self.items into two parser instances to use as learning and
        training data.
        @param fraction (float): fraction of items to keep in first of 2 instances
        Returns 2 Parser objects. NOTE: items in parser objects are references to
        self.items. So any changes to items in self.items or in the 2 parsers
        will be reflected.
        """
        samples = np.random.choice(self.items, len(self.items), replace=False)
        n1 = np.floor(len(self.items) * fraction)
        s1 = samples[:n1]
        s2 = samples[n1:]
        p1 = Parser(client=self.client, items=s1)
        p2 = Parser(client=self.client, items=s2)
        return p1, p2
