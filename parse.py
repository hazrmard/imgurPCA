from __future__ import print_function
from __future__ import unicode_literals
from imgurpython import ImgurClient
from post import Post
from user import User
import utils


class Parser(object):

    def __init__(self, *args, **kwargs):
        utils.set_up_client(self, **kwargs)
        for attr in kwargs:
            setattr(self, attr, kwargs[attr])
