from __future__ import unicode_literals
from imgurpython import ImgurClient
from config import InvalidArgument

def flatten(container, lvl=1):
    """convert arbitrarily nested arrays of comments into a flat array
    Acts as a generator. Returns a tuple of (comment object, level)
    """
    for i in container:
        yield (i, lvl)              # yield current comment
        if isinstance(i.children, (list,tuple)) and i.children:
            for j in flatten(i.children, lvl+1):
                yield j             # yield flattened out children


def sanitize(sentence):
    """takes a sentence and returns a list of words
    """
    sentence = sentence.lower() # to lower case
    words = sentence.split()    # split on whitespace
    return words


def set_up_client(instance, **kwargs):
    if 'cid' in kwargs and 'cs' in kwargs:
        instance.client = ImgurClient(kwargs['cid'], kwargs['cs'])
    elif 'client' in kwargs:
        instance.client = kwargs['client']
    else:
        raise InvalidArgument('Either include client=ImgurClient()'
                            ' instance, or cid=CLIENT_ID and cs=CLIENT_SECRET')


def num_lines(fname):
    """returns the number of lines in a file.
    @param fname (str): name of file
    """
    with open(fname, 'rb') as f:
        return sum((1 for line in f))


def is_url(path):
    """returns True of path starts with [http | ftp ][s]
    @param path (str): url or file path
    """
    return path.startswith('http') or \
            path.startswith('https') or \
            path.startswith('ftp') or \
            path.startswith('ftps')
