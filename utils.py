

def flatten(container, lvl=1):     # http://stackoverflow.com/a/10824420/4591810
    """convert arbitrarily nested arrays of comments into a flat array
    """
    for i in container:
        if isinstance(i.children, (list,tuple)):
            lvl += 1
            for j in flatten(i.children, lvl):
                yield (j, lvl)
        else:
            yield (i, lvl)


def sanitize(sentence):
    """takes a sentence and returns a list of words
    """
    sentence = sentence.lower() # to lower case
    words = sentence.split()    # split on whitespace
    return words
