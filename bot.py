from __future__ import print_function
from __future__ import unicode_literals
import utils
import config
import webbrowser

# The Bot class acts as a user agent. It can perform scheduled tasks when some
# condition is met. It can also post on behalf of a user.

class Bot:

    def __init__(self, *args, **kwargs):
        """
        @param access_token (str): OPTIONAL. access token for user
        @param refresh_token (str): OPTIONAL. refresh token for user
        @param cid (string): client id, use with 'cs'
        @param cs (string): client secret, use with 'cid'.
        OR:
        @param client (ImgurClient): imgurpython.ImgurClient instance
        """
        utils.set_up_client(self, **kwargs)
        self.access_token = None
        self.refresh_token = None

        for attr in kwargs:
            setattr(self, attr, kwargs[attr])


    def auth_url(self, launch=False):
        """returns a url the user must go to to obtain a pin for authentication.
        Only use this func and authorize() if acting on behalf of a user and not
        anonymously.
        """
        url = self.client.get_auth_url('pin')
        if launch:
            webbrowser.open(url)
        return url


    def authorize(self, pin, credfile=None):
        """get access and refresh tokens using the pin obtained from get_auth_url
        Only to be called if access_token and refresh_token were not provided during
        instantiation.
        @param pin (str): the pin obtained from going to auth url
        @param credfile (str): OPTIONAL. name of file to store tokens into
        """
        cred = self.client.authorize(pin, 'pin')
        self.access_token = cred['access_token']
        self.refresh_token = cred['refresh_token']
        self.client.set_user_auth(self.access_token, self.refresh_token)
        if credfile is not None:
            with open(credfile, 'w') as f:
                f.write(self.access_token + '\n')
                f.write(self.refresh_token + '\n')


    def load_credentials(self, credfile):
        """load access and refresh tokens from file. Either use this or use
        get_auth_url() and authorize().
        @param credfile (str): name of file containing credentials
        """
        with open(credfile, 'r') as f:
            self.access_token = f.readline()[:-1]   # -1 for \n character
            self.refresh_token = f.readline()[:-1]
        self.client.set_user_auth(self.access_token, self.refresh_token)
