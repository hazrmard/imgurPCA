from __future__ import unicode_literals
from __future__ import absolute_import
from imgurpca.post import Post
import imgurpca.utils as utils
import imgurpca.config as config

# User is a subclass of Post which represents comments made by an imgur user.
# Each user is identified by the url attribute (alias: username) which must be
# provided at intantiation along with client/id and secret.

class User(Post):

    def __init__(self, url, *args, **kwargs):
        """Instantiate a User object.
        @param url (str): the username of an account. It is called 'url' in the
                        API data model.
        @param cid (string): client id, use with 'cs'
        @param cs (string): client secret, use with 'cid'.
        OR:
        @param client (ImgurClient): imgurpython.ImgurClient instance
        """
        super(User, self).__init__(None, *args, **kwargs)    # id=None, to be set later

        del self.user                       # redundant attrs from inheritance

        self.url = url                      # = username
        self.reputation = 1                 # = points (alias for inheritance)
        self.posts = []                     # list of Gallery Image/Album/GalleryAlbum objects, see API
        self.favourites = []                # list of Gallery Image/Album/GalleryAlbum objects, see API

    @property
    def username(self):                     # that is what url is
        return self.url

    @property
    def points(self):                       # to work nicely with Post().points
        return self.reputation

    @property
    def network(self):
        return self.get_post_ids()


    def download(self, pages=0):
        """download the relevant gallery post, favourites, comments, and user data
        based on self.username.
        @param pages (int/tuple): page number or range of pages (inclusive) to get
        """
        account_obj = self.client.get_account(self.username)
        for attr in account_obj.__dict__:
            setattr(self, attr, account_obj.__dict__[attr])
        if isinstance(pages, int):
            pages = (pages, pages+1)
        for i in range(*pages):
            res = self.client.get_account_submissions(self.username, page=i)
            if len(res)==0:
                break
            self.posts.extend(res)
        for i in range(*pages):
            res = self.client.get_account_comments(self.username, page=i)
            if len(res)==0:
                break
            self.comments.extend(res)
        for i in range(*pages):
            res = self.client.get_gallery_favorites(self.username, page=i)
            if len(res)==0:
                break
            self.favourites.extend(res)


    def get_post_ids(self):
        """return string ids for posts by user. Requires download() first.
        """
        return [p.id for p in self.posts]

    def get_user_ids(self):
        raise config.FunctionNotApplicable('Use get_post_ids() for User objects')


    def generate_word_counts(self, comment_votes=True, *args, **kwargs):
        """same as Post.generate_word_counts, but with no option for child_comments
        or comment level. From the user perspective all comments are equally
        weighed.
        @param comment_votes (bool): whether to pass comment votes to self.word_weight
                                    sends 1 is False.
        *args and **kwargs added to allow for same function signature as Post func.
        """
        super(User, self).generate_word_counts(child_comments=False,
                                comment_level=False, comment_votes=comment_votes)
