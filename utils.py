from __future__ import unicode_literals

def flatten(container, lvl=1):
    """convert arbitrarily nested arrays of comments into a flat array
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
