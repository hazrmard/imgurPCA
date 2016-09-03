from __future__ import print_function
from __future__ import unicode_literals
from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientRateLimitError, ImgurClientError
from post import Post
from user import User
from query import Query
from parallel import Parallel
import utils


class Parser(object):

    class Downloader(Parallel):
        def parallel_process(self, pkg, common):
            pkg.download()


    def __init__(self, nthreads=8, *args, **kwargs):
        """
        @param cid (string): client id, use with 'cs'
        @param cs (string): client secret, use with 'cid'.
        OR:
        @param client (ImgurClient): imgurpython.ImgurClient instance
        """
        utils.set_up_client(self, **kwargs)
        self.items = []
        self.nthreads = nthreads
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

    def download(self):
        """downloads whatever items (User/Post objects) are placed in self.items
        """
        D = Parser.Downloader(self.items, nthreads=self.nthreads)
        try:
            D.start()
            D.wait_for_threads()
        except ImgurClientRateLimitError:
            print('Rate limit exceeded:\n' + str(self.client.credits))


    def get_posts(self, query):
        """instantiates posts to self.items.
        @param query (Query): a Query instance. See query.py.
        """
        source_func = self._query_to_client[query.mode]
        self.items = source_func(**query.content)
        self.items = [Post(client=self.client, **p.__dict__) for p in self.items]


    def populate_posts(self, posts):
        """instantiate Post objects to self.items given post ids
        @param posts (list): a collection of post ids to download
        """
        self.items = [Post(client=self.client, id=p) for p in posts]


    def populate_users(self, users):
        """instantiate User objects to self.items, given post ids
        @param users (list): a collection of user ids (usernames) to download
        """
        self.items = [User(client=self.client, url=u) for u in users]
