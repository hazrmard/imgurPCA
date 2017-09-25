# for any utility functions that apply strictly to the imgur API and not generally
# to parsing/learning etc.
from imgurpython import ImgurClient
from . import config

def set_up_client(instance, **kwargs):
    """sets up self.client with ImgurClient instance given either client secret
    and client id or an ImgurClient instance.
    Raises InvalidArgument if ('cs' and 'cid') or 'client' keyword args not present.
    """
    if 'cid' in kwargs and 'cs' in kwargs:
        instance.client = ImgurClient(kwargs['cid'], kwargs['cs'])
    elif 'client' in kwargs:
        instance.client = kwargs['client']
    else:
        raise config.InvalidArgument('Either include client=ImgurClient()'
                            ' instance, or cid=CLIENT_ID and cs=CLIENT_SECRET')
