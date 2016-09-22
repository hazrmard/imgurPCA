from __future__ import unicode_literals
from __future__ import absolute_import
from imgurpython import ImgurClient
from imgurpca.base import config

def flatten(container, lvl=1, accessor=lambda x: x.children):
    """convert arbitrarily nested arrays of comments into a flat array
    Acts as a generator. Returns a tuple of (comment object, level)
    @param accessor (func): OPTIONAL. Returns a reference to nested elements.
    @param lvl (int): nesting level. 1 is top level. Do not change when calling.
    """
    for i in container:
        if not isinstance(i, (list,tuple)):
            yield (i, lvl)              # yield current comment
        if isinstance(accessor(i), (list,tuple)) and accessor(i):
            for j in flatten(accessor(i), lvl+1, accessor):
                yield j             # yield flattened out children


def sanitize(sentence):
    """takes a sentence and returns a list of words
    """
    sentence = sentence.lower() # to lower case
    words = sentence.split()    # split on whitespace
    return words


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
