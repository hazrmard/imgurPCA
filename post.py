from imgurpython import ImgurClient
import utils
import config
import numpy as np

class Post(object):

    def __init__(self, id, **kwargs):
        self.id = id                    # str
        self.user = None                # account object (see imgur API doc.)
        self.comments = []              # array of comment objects (see imgur API doc.)
        self.wordcount = np.array([], dtype=config.DT_WORD_COUNT)

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
        post_obj = self.client.gallery_item(self.id)
        for attr in post_obj.__dict__:
            setattr(self, attr, post_obj.__dict__[attr])

        if post_obj.account_url:
            self.user = self.client.get_account(post_obj.account_url)

        self.comments = self.client.gallery_item_comments(self.id)


    def generate_word_counts(self):
        pass
