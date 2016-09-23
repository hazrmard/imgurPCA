from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from imgurpython.imgur.models.image import Image
from imgurpython.imgur.models.album import Album
from imgurpython.imgur.models.gallery_album import GalleryAlbum
from imgurpython.imgur.models.account import Account
from imgurpython.client import ImgurClientRateLimitError, ImgurClientError
from imgurpca import Post
from imgurpca import User
from imgurpca import Query
from imgurpca import imutils
from imgurpca.base import Molecular
from imgurpca import utils
from imgurpca import config
import numpy as np
import sys

# The Parser class performs operations on a collection of Post or User objects
# stored in Parser.items. Parser can either populate posts from IDs or from a
# Query object. In addition it performs feature selection operations on the
# downloaded data. Parser.items can contain all properly subclassed instances of
# base.Atomic class (e.g. User and Post).
# Parser is subclassed from base.Molecular.

class Parser(Molecular):

    class Downloader(Molecular.Downloader):
        def parellel_process(self, pkg, common):
            try:
                super(Downloader, self).parallel_process(pkg, common)
            except ImgurClientRateLimitError:
                print('Rate limit exceeded.', file=sys.stderr)


    def __init__(self, nthreads=8, *args, **kwargs):
        """
        @param nthreads (int): number of threads to run content downloads on.
        @param cid (string): client id, use with 'cs'
        @param cs (string): client secret, use with 'cid'.
        OR:
        @param client (ImgurClient): imgurpython.ImgurClient instance
        """
        imutils.set_up_client(self, **kwargs)
        super(Parser, self).__init__(**kwargs)

        self._query_to_client = {Query.GALLERY_TOP: self.client.gallery,
                                Query.GALLERY_HOT: self.client.gallery,
                                Query.GALLERY_USER: self.client.gallery,
                                Query.SUBREDDIT: self.client.subreddit_gallery,
                                Query.TAG: self.client.gallery_tag,
                                Query.CUSTOM: self.client.gallery_search,
                                Query.RANDOM: self.client.gallery_random,
                                Query.MEMES: self.client.memes_subgallery}


    def content(self, flatten=True, accessor=lambda x:x.children):
        """returns a generator (optionally flattened) of content attributes of
        User/Post objects in self.items.
        @param flatten (bool): whether to flatten nested comments
        @param accessor (func): a function that returns reference to nested
                                elements.
        Returns a list (nested if flatten=False) of comment objects.
        """
        return super(Parser, self).content(flatten, accessor)


    def get(self, query, pages=0):
        """instantiates posts to self.items based on a query.
        @param query (Query): a Query instance. See query.py.
        @param pages (int/tuple): page number or range of pages (inclusive) to get
        """
        source_func = self._query_to_client[query.mode]
        self.items = []
        try:
            if isinstance(pages, int):
                self.items.extend(source_func(page=pages, **query.content))
            elif isinstance(pages, (tuple,list)):
                for i in range(*pages):
                    self.items.extend(source_func(page=i, **query.content))
        except ImgurClientRateLimitError:
            print('Rate limit exceeded.', file=sys.stderr)
        finally:
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
