from __future__ import unicode_literals
from __future__ import absolute_import
from imgurpca import utils
from imgurpca import config
import numpy as np

# Atomic is the base class that represents a single data point for learning
# purposes. It is useful when it is derived (see Post and User classes). All
# methods with a 'pass' in their bodies need to be overwritten for full
# compatibility.

class Atomic(object):

    def __init__(self, **kwargs):
        self.wordcount = None       # np array of dtype=config.DT_WORD_WEIGHT
        self.word_weight = config.DEFAULT_WORD_WEIGHT

        for attr in kwargs:
            setattr(self, attr, kwargs[attr])

    @property
    def words(self):
        return self.wordcount['word']

    @property
    def weights(self):
        return self.wordcount['weight']

    @property
    def content(self):
        # return list/generator of source[s] of self.wordcount
        pass


    def download(self):
        # function that populates whatever is it self.content returns
        pass


    def generate_word_counts(self):
        # populate self.wordcount with a np array of dtype=config.DT_WORD_WEIGHT
        # using self.content
        pass


    def filter_by_weight(self, minimum, maximum, reverse=False):
        """filter out words in self.wordcount with minumum <= weights <= maximum
         less than min. reverse=True filters out words with max < weights < min
        """
        if minimum>maximum:
            raise ValueError('Minimum is less than maximum.')
        if not reverse:
            self.wordcount = self.wordcount[self.wordcount['weight']<=maximum]
            self.wordcount = self.wordcount[self.wordcount['weight']>=minimum]
        else:
            temp = self.wordcount[self.wordcount['weight']>maximum]
            self.wordcount = self.wordcount[self.wordcount['weight']<minimum]
            self.wordcount = np.concatenate((self.wordcount, temp), axis=0)


    def filter_by_word(self, words, reverse=False):
        """if reverse=False, only keep elements in wordcount present in words,
        else only keep elements in wordcount not in words.
        @param words (list/array): a list of words in unicode
        """
        self.wordcount = self.wordcount[np.in1d(self.wordcount['word'], words,
                                        assume_unique=True, invert=reverse)]


    def sort_by_word(self):
        self.wordcount.sort(order=['word'])


    def sort_by_weight(self):
        self.wordcount.sort(order=['weight'])


    def sort(self):
        """sorts according to whatever default sort order is set. Default order is
        used by Parser.consolidate() and Learner.project() functions as well.
        """
        self.wordcount.sort(order=[config.DEFAULT_SORT_ORDER])
