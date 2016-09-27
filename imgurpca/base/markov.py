from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from imgurpca.base import Molecular
from imgurpca.base import Atomic
from imgurpca.base import config
from collections import deque
import re
import random

# the Markov class generates random text responses based on an input corpus.


class Markov(object):

    def __init__(self, source, order=2, *args, **kwargs):
        self.order = order
        self.source = source
        self.chain = {}

        # delimiters indicate what to split the text on
        self.regex_delimiters = [r'\s']     # These are not escaped for re and used as-is
        self.delimiters = ['.', ',', ';', '-', ':', '?','!'] # These are escaped
        self.delimiter_pattern = None       # set by generate_chain(), used by re module

        # stopchars indicate the end of a sentence, should be a subset of delimiters
        self.regex_stopchars = ['\n']       # these are not escaped for re and used as-is
        self.stopchars = ['.', '!', '?']    # these are escaped by re.escape()
        self.stop_pattern = None            # set by random_walk, used by re module

        self.spacechar = ' '

        for attr in kwargs:
            setattr(self, attr, kwargs[attr])


    @property
    def plaintext(self):
        """overwrite this function to return a combined string of all text in the
        source.
        Returns a string.
        """
        return self.source.content


    def generate_chain(self):
        """Creates a dictionary of prefixes and possible suffixes from the
        plaintext generated from source. Dictionary keys are tuples of length
        self.order, keys map to lists of single words.
        """
        self.delimiter_pattern = pattern = '([' + re.escape(''.join(self.delimiters))\
                                                + ''.join(self.regex_delimiters) + ']+)'
        words = [self.stopchars[0]] + \
                    re.split(pattern, self.plaintext)       # split on delimiters
        key = deque(words[:self.order])
        for i, w in enumerate(words[self.order:]):
            tkey = tuple(key)
            try:
                self.chain[tkey].append(w)
            except KeyError:
                self.chain[tkey] = [w]
            key.append(w)
            key.popleft()


    def random_walk(self, begin=None, times=1):
        """given a starting position as a key to self.chain or a string, output a
        string of words in self.chain joined by self.spacechar. The output terminates
        when any character in self.stopchars/self.regex_stopchars is encountered.
        This is repeated by 'times'
        Returns a string.
        """
        if len(self.chain)==0:
            raise config.PrematureFunctionCall('Generate chain first.')

        self.stop_pattern = '[' + re.escape(''.join(self.stopchars)) + ''.join(self.regex_stopchars) + ']+'
        pattern = re.compile(self.stop_pattern)

        if isinstance(begin, basestring):   # if string, convert to tuple
            begin = re.split(self.delimiter_pattern, begin)
            if len(begin)<self.order:       # if tuple size is smaller than key size
                sbegin = set(begin)         # find a key w/ similar words as tuple
                begin = None                # if not, find a random key
                for key in self.chain.keys():
                    if pattern.search(key[0]) and sbegin.intersection(set(key)):
                        begin = key
                        break

        if begin is None:       # select a random start position.
            begin = ('',)
            keys = self.chain.keys()
            i=0
            while not pattern.search(begin[0]) and i<len(keys):
                begin = random.choice(keys)
                i+=1

        out = list(begin)
        for i in range(times):
            while True :   # while not stop chars at end,
                key = tuple(out[-self.order:])
                nex = self.chain.get(key)
                if nex:
                    out.append(random.choice(nex))
                else:
                    out.append(random.choice(self.chain[random.choice(self.chain.keys())]))
                if pattern.search(out[-1]):
                    break

        return self.spacechar.join(out)


    def sanitize(self, text):
        """Takes the output of random_walk() and sanitizes it. Removes double
        self.spacechars, stop_pattern from beginning of string, spaces before
        stop_pattern.
        """
        self.stop_pattern = '[' + re.escape(''.join(self.stopchars)) + ''.join(self.regex_stopchars) + ']+'
        out = re.sub('^'+self.stop_pattern, '', text)   # remove stopchars from beginning
        out = re.sub(self.spacechar+'+', self.spacechar, out)   # remove repeated spaces
        out = re.sub(self.spacechar+'('+self.stop_pattern+')', r'\1', out)  # remove spaces before stopchars
        return out
