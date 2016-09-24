from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from imgurpython.client import ImgurClientError
from imgurpca import utils
from imgurpca import config
from imgurpca.base import Electronic
from imgurpca import imutils
from glob import glob
import threading
import time

# The Bot class acts as a user agent. It can perform scheduled tasks when some
# condition is met. It can also post on behalf of a user. The Bot operates in
# 2 modes: Authenticated and Anonymous. If credentials are loaded or obtained
# using pin authorization, then Bot is Authenticated. Bot exposes the entire
# API of imgurpython through Bot.client which is an ImgurClient instance.
# Bot is subclassed from base.Electronic.

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


    @property
    def auth_url(self):
        """returns a url the user must go to to obtain a pin for authentication.
        Only use this func and authorize() if acting on behalf of a user and not
        anonymously.
        @param launch (bool): Whether to open the link in a browser automatically.
        Returns the url to obtain the pin for authorization.
        """
        return self.client.get_auth_url('pin')


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
            self.share(res['id'], res['title'])
            res['in_gallery'] = True
        return res


    def delete_image(self, img_id):
        """deletes an image from imgur.
        @param img_id (str): ID of image (if bot is authenticated) or delete hash
                        (if bot is anonymous). Delete hash is contained in the
                        dict returned from upload_image().
        Returns boolean indicating success.
        """
        return self.client.delete_image(img_id)


    def create_album(self, imgids, share=False, **kwargs):
        """create an album from images already uploaded to imgur.
        @param imgids (list/tuple): list of image ids
        """
        pass


    def delete_album(self, post_id):
        pass


    def unshare(self, post_id):
        """remove shared image/album from gallery.
        @param post_id (str): ID of image/album
        Returns boolean to indicate unshare success.
        """
        return self.client.remove_from_gallery(post_id)


    def share(self, post_id, title=''):
        """put the image on imgur gallery
        @param itemid (str): ID of image/album
        @param title (str): Title under which to share
        Returns bool to indicate share success.
        """
        if self.anon:
            raise config.PrematureFunctionCall('Authenticate Bot first.')
        return self.client.share_on_imgur(post_id, title)


    def _vote(self, post_id, what):
        if self.anon:
            raise config.PrematureFunctionCall('Authenticate Bot first.')
        return self.client.gallery_item_vote(post_id, what)


    def upvote(self, post_id):
        """post an upvote on a gellery image/album. Bot must be Authenticated.
        @param post_id (str): id of item.
        Returns API response as a dict.
        """
        return self._vote(post_id, 'up')


    def downvote(self, post_id):
        """post a downvote on a gellery image/album. Bot must be Authenticated.
        @param post_id (str): id of item.
        Returns API response as a dict.
        """
        return self._vote(post_id, 'down')


    def get_notifications(self, new=True, markread=True):
        """get a list of notification objects for the current account.
        Requires authentication.
        @param new (bool): only get unread notifications
        @param markread (bool): mark downloaded notifications as read
        Returns a dictionary with keys 'messages' and 'replies'. Messages and
        replies are of the notification data model. Notification.content is
        a comment object for replies and a message object for messages.
        """
        if self.anon:
            raise config.PrematureFunctionCall('Authenticate Bot first.')
        res = self.client.get_notifications(new=new)
        try:
            if len(res) and markread:
                ids = [str(n.id) for n in (res['replies'] + res['messages'])]
                # ** getting ImgurClientError (400): IDs required with this**
                self.client.mark_notifications_as_read(ids)
        except ImgurClientError as e:
            raise e
        finally:
            return res


    def post_comment(self, post_id, comment):
        """post a comment on a gallery item.
        @param post_id (str): id of post on gallery.
        @param comment (str): comment body
        Returns API response as a dict containing comment id.
        """
        if self.anon:
            raise config.PrematureFunctionCall('Authenticate Bot first.')
        return self.client.gallery_comment(post_id, comment)


    def post_reply(self, comment_id, post_id, comment):
        """Post a reply to a comment on a gallery post.
        @param comment_id (str): id of comment to reply to
        @param post_id (str): id of post on gallery containing the comment.
        @param comment (str): comment body
        Returns API response as a dict containing reply id.
        """
        if self.anon:
            raise config.PrematureFunctionCall('Authenticate Bot first.')
        return self.client.post_comment_reply(comment_id, post_id, comment)


    def send_message(self, recipient, message):
        """send a direct message to a user.
        @param recipient (str): target username
        @param message (str): message body
        Returns API response: a boolean.
        """
        if self.anon:
            raise config.PrematureFunctionCall('Authenticate Bot first.')
        return self.client.create_message(recipient, message)


    def conversation_list(self):
        """get a list of conversation objects. See imgur API data models.
        Returns a list of conversation objects. Conversation objects only
        contain portion of the last message from the other user.
        For more messages, use get_conversation() to get a single conversation
        thread.
        """
        if self.anon:
            raise config.PrematureFunctionCall('Authenticate Bot first.')
        return self.client.conversation_list()


    def get_conversation(self, conv_id, page=1):
        """get a single conversation thread.
        @param conv_id (str): conversation id
        @param page (int): page number of conversation. starts from 1.
        Returns a conversation object with messages stored in messages attribute.
        Messages are message objects (see API data model)
        """
        if self.anon:
            raise config.PrematureFunctionCall('Authenticate Bot first.')
        return self.client.get_conversation(conv_id, page)
