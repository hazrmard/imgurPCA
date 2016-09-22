from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from imgurpca import utils
from imgurpca import config
from imgurpca.base import Electronic
from imgurpca import imutils
import webbrowser
from glob import glob
import threading
import time

# The Bot class acts as a user agent. It can perform scheduled tasks when some
# condition is met. It can also post on behalf of a user. The Bot operates in
# 2 modes: Authenticated and Anonymous. If credentials are loaded or obtained
# using pin authorization, then Bot is Authenticated. Bot exposes the entire
# API of imgurpython through Bot.client which is an ImgurClient instance.
# Bot is subclassed from Electronic.

class Bot(Electronic):

    def __init__(self, *args, **kwargs):
        """
        @param access_token (str): OPTIONAL. access token for user
        @param refresh_token (str): OPTIONAL. refresh token for user
        @param cid (string): client id, use with 'cs'
        @param cs (string): client secret, use with 'cid'.
        OR:
        @param client (ImgurClient): imgurpython.ImgurClient instance
        If refresh_token and access_token are included in keyword arguments,
        Bot is automatically Authenticated.
        """
        self.access_token = None
        self.refresh_token = None
        self.anon = True

        if ('access_token' in kwargs) and ('refresh_token' in kwargs):
            self._authenticate(self.access_token, self.refresh_token)

        imutils.set_up_client(self, **kwargs)
        super(Bot, self).__init__(**kwargs)


    def _authenticate(self, access_token, refresh_token):
        """sets up self.client with access and refresh tokens"""
        self.client.set_user_auth(self.access_token, self.refresh_token)
        self.anon = False


    def auth_url(self, launch=False):
        """returns a url the user must go to to obtain a pin for authentication.
        Only use this func and authorize() if acting on behalf of a user and not
        anonymously.
        @param launch (bool): Whether to open the link in a browser automatically.
        Returns the url to obtain the pin for authorization.
        """
        url = self.client.get_auth_url('pin')
        if launch:
            webbrowser.open(url)
        return url


    def authorize(self, pin, credfile=None):
        """get access and refresh tokens using the pin obtained from get_auth_url.
        This Authenticates the Bot.
        @param pin (str): the pin obtained from going to auth url
        @param credfile (str): OPTIONAL. name of file to store tokens into
        """
        cred = self.client.authorize(pin, 'pin')
        self.access_token = cred['access_token']
        self.refresh_token = cred['refresh_token']
        self._authenticate(self.access_token, self.refresh_token)
        if credfile is not None:
            with open(credfile, 'w') as f:
                f.write(self.access_token + '\n')
                f.write(self.refresh_token + '\n')


    def load_credentials(self, credfile):
        """load access and refresh tokens from file. This Authenticates the Bot.
        Either use this OR use get_auth_url() and authorize() together.
        @param credfile (str): name of file containing credentials
        """
        with open(credfile, 'r') as f:
            self.access_token = f.readline()[:-1]   # -1 for \n character
            self.refresh_token = f.readline()[:-1]
        self._authenticate(self.access_token, self.refresh_token)


    def upload_image(self, imgpath, share=False, **kwargs):
        """upload image to imgur from either a URL or filepath.
        @param imgpath (str): local path or URL to image file
        @param share (bool): whether to post to gallery. Only if Authenticated.
        @param title (str): OPTIONAL. Title of post
        @param description (str): OPTIONAL. Description of post
        @param album (str): OPTIONAL. Album id to add image to. Or delete hash
                        in case anonymous.
        @param name (str): OPTIONAL. Name of image file.
        See ImgurClient.allowed_image_fields for allowed keywords.
        Returns a dict containing image location, id, title etc.
        """
        if utils.is_url(imgpath):
            res = self.client.upload_from_url(imgpath, config=kwargs, anon=self.anon)
        else:
            res = self.client.upload_from_path(imgpath, config=kwargs, anon=self.anon)
        if share:
            if self.anon:
                raise config.PrematureFunctionCall('Authenticate Bot first.')
            self.client.share_on_imgur(res['id'], res['title'])
            res['in_gallery'] = True
        return res


    def delete_image(self, imgid):
        """deletes an image from imgur.
        @param imgid (str): ID of image (if bot is authenticated) or delete hash
                        (if bot is anonymous). Delete hash is contained in the
                        dict returned from upload_image().
        """
        self.client.delete_image(imgid)


    def create_album(self, imgids, share=False, **kwargs):
        """create an album from images already uploaded to imgur.
        @param imgids (list/tuple): list of image ids
        """
        pass


    def delete_album(self, itemid):
        pass


    def unshare(self, itemid):
        """remove shared image/album from gallery.
        @param itemid (str): ID of image/album
        """
        self.client.remove_from_gallery(itemid)


    def _vote(itemid, what):
        if self.anon:
            raise config.PrematureFunctionCall('Authenticate Bot first.')
        self.client.gallery_item_vote(itemid, what)


    def upvote(self, itemid):
        """post an upvote on a gellery image/album. Bot must be Authenticated.
        @param itemid (str): id of item.
        """
        self._vote(itemid, 'up')


    def downvote(self, itemid):
        """post a downvote on a gellery image/album. Bot must be Authenticated.
        @param itemid (str): id of item.
        """
        self._vote(itemid, 'down')
