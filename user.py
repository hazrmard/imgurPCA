from __future__ import unicode_literals
from post import Post
import utils
import config

class User(Post):

    def __init__(self, url, *args, **kwargs):
        super(User, self).__init__(None, *args, **kwargs)    # id=None, to be set later

        del self.user                       # redundant attrs from inheritance

        self.url = url                      # = username
        self.reputation = 0                 # = points (alias for inheritance)
        self.posts = []                     # list of Gallery Image/Album objects, see API

    @property
    def username(self):                     # that is what url is
        return self.url

    @property
    def points(self):                       # to work nicely with Post().points
        return self.reputation


    def download(self):
        """download the relevant gallery post, comments, and user data based on
        self.id.
        """
        account_obj = self.client.get_account(self.url)
        for attr in account_obj.__dict__:
            setattr(self, attr, account_obj.__dict__[attr])

        self.posts = self.client.get_account_submissions(self.url)
        self.comments = self.client.get_account_comments(self.url)


    def get_post_ids(self):
        """return string ids for posts by user. Requires download() first.
        """
        return [p.id for p in self.posts]

    def get_user_ids(self):
        raise config.FunctionNotApplicable('Use get_post_ids() for User objects')


    def generate_word_counts(self, comment_votes=True):
        super(User, self).generate_word_counts(child_comments=False,
                                comment_level=False, comment_votes=comment_votes)
