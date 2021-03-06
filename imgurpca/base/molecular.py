from __future__ import unicode_literals
from __future__ import absolute_import
from . import utils
from . import config
from . import Parallel
import numpy as np

# The Molecular class (as in: a collection of atoms) is a container class for
# Atomic subclasses. It can perform cumulative filtration and feature selection
# functions. Atomic objects are stored in Molecular.atoms. The get() method should
# be overwritten in case the sources can be obtained through an API (see Parser).

class Molecular(object):

    class Downloader(Parallel):
        def parallel_process(self, pkg, common):
            pkg.download()


    def __init__(self, **kwargs):
        self.items = []                 # a list of Atomic subclassed objects
        self.nthreads = 1
        self.wordcount = None
        self._consolidated = False      # flag to signal if all wordcounts sorted
        for attr in kwargs:
            setattr(self, attr, kwargs[attr])


    def content(self, flatten=True, accessor=lambda x:x):
        """returns a generator containing list[s] of content objects for all items.
        [[post1.content], [post2.content]...[postn.content]]
        @param flatten (bool): whether to flatten lists.
        """
        for item in self.items:
            if flatten:
                for c, level in utils.flatten(item.content, accessor=accessor):
                    yield c
            else:
                for c in item.content:
                    yield c

    @property
    def words(self):
        return self.wordcount['word']

    @property
    def weights(self):
        return self.wordcount['weight']


    def download(self):
        """downloads whatever items (User/Post objects) are placed in self.items
        """
        D = self.__class__.Downloader(self.items, nthreads=self.nthreads)
        D.start()
        D.wait_for_threads()


    def get(self, query,):
        """instantiates items to self.items. Items should be subclasses of Atomic.
        """
        pass


    def consolidate(self, words=None, reverse=False):
        """Generate a cumulative wordcount from the items' wordcounts. Add 0-weight
        words to items' wordlists so all items have the same set of words. Sort
        cumulative wordlist and item wordlists (by word) so index positions are
        identical.
        @param words (list/array): OPTIONAL - a list of words to keep and consolidate.
                                Otherwise, generates list of unique words from
                                all wordcounts in self.items
        @param reverse (bool): True->filter out 'words', use everything else,
                               False->only use 'words', filter out everything else.
                               Only matters if words provided.
        """
        if len(self.items)==0:
            raise config.PrematureFunctionCall('No User/Post objects in self.items.')
        word_dict = {}
        if words is not None:
            if not reverse:                         # i.e. if only 'words' MUST be in wordcount
                word_dict = {w:0 for w in words}    # then word_dict initialized w/ 'words'
            for item in self.items:                 # filter (in/out) words from items
                item.filter_by_word(words, reverse)

        for item in self.items:
            if item.wordcount is None:
                raise config.PrematureFunctionCall('Generate wordcounts first.')
            for w in item.wordcount:
                try:                    # if word already exists, increment weight
                    word_dict[w['word']] += w['weight']
                except KeyError:        # else add word if a strict word list not provided
                    if words is None or reverse:
                        word_dict[w['word']] = w['weight']
        self.wordcount = np.array(list(word_dict.items()), dtype=config.DT_WORD_WEIGHT)
        self.wordcount.sort(order=[config.DEFAULT_SORT_ORDER])

        for item in self.items:
            zero_words = np.setdiff1d(self.words, item.words, assume_unique=True)
            zero_wordcounts = np.array(list(zip(zero_words, np.zeros(len(zero_words)))), dtype=config.DT_WORD_WEIGHT)
            item.wordcount = np.append(item.wordcount, zero_wordcounts)
            item.sort()     # using default sort order
        self._consolidated = True


    def get_baseline(self):
        """given the wordcounts for all self.items, find the average weight
        and variance of each word. This can then be used to filter out frequent
        or consistently appearing words to reduce bloat. Can only be called after
        consolidation.
        Returns a tuple -> (average scores, variances) of 1D np arrays where
        order corresponds to self.words.
        """
        if not self._consolidated:
            raise config.PrematureFunctionCall('Consolidate first.')
        matrix = np.zeros((len(self.items), len(self.weights)))
        for i, item in enumerate(self.items):
            matrix[i,:] = item.weights
        means = np.mean(matrix, axis=0)
        variances = np.var(matrix, axis=0)
        return (means, variances)


    def split(self, fraction=0.5):
        """split self.items into two Molecular instances to use as learning and
        training data.
        @param fraction (float): fraction of items to keep in first of 2 instances
        Returns 2 lists of Atomic. NOTE: items in Molecular objects are references to
        self.items. So any changes to items in self.items or in the 2 Moleculars
        will be reflected.
        """
        samples = np.random.choice(self.items, len(self.items), replace=False)
        n1 = int(np.floor(len(self.items) * fraction))
        s1 = samples[:n1]
        s2 = samples[n1:]
        return s1, s2
