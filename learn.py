from __future__ import print_function
from __future__ import unicode_literals
from post import Post
from user import User
from parse import Parser
import utils
import config
import numpy as np


class Learner(object):

    def __init__(self, *args, **kwargs):
        """provide a source as a keyword argument
        @param parser (Parser): a Parser instance
        OR
        @param post (Post): a Post instance
        OR
        @param user (User): a User instance
        """
        if 'parser' in kwargs:
            self.parser = kwargs['parser']
            self._stype = 'parser'
        elif 'post' in kwargs:
            self.post = kwargs['post']
            self._stype = 'post'
        elif 'user' in kwargs:
            self.user = kwargs['user']
            self._stype = 'user'
        else:
            raise AttributeError('Include parser, post, or user key/value pair.')

        self.axes = None        # np.array

        for attr in kwargs:
            setattr(self, attr, kwargs[attr])

    @property
    def source(self):
        """returns a User, Post, or Parser object depending on what Learner was
        instantiated with.
        """
        if self._stype=='parser':
            return self.parser
        elif self._stype=='post':
            return self.post
        elif self._stype=='user':
            return self.user
        else:
            raise AttributeError('No source (parser, post, user) found.')

    @property
    def words(self):
        """returns an array of words in the source's wordcount. Useful for finding
        what words positions represent in covariance matrice, eigenvectors etc.
        """
        return self.source.wordcount['word']

    def get_eigenvectors(self):
        """get the eignevectors describing the wordcounts of the items in the
        Parser given to Learner. For comment-wise vectors, use get_comment_eigenvectors()
        """
        if self._stype=='parser':
            if self.source._consolidated:
                counts = np.vstack((item.wordcount['weight'] for item in self.source.items))
                cov = np.cov(counts)
                eiw, eiv = np.linalg.eig(cov)       # eiw=e-vals, eiv=e-vectors
                order = eiw.argsort()[::-1]
                eiw = eiw[order]
                eiv = eiv[:, order]                 # vals/vecs ordered by largest eval
                self.axes = eiv
            else:
                raise config.PrematureFunctionCall('Consolidate Parser first.')
        else:
            raise Exception('Use get_comment_eigenvectors for Post/User sources.')


    def get_comment_eigenvectors(self, child_comments=False, comment_votes=True,
                            comment_level=True):
        """get eigenvectors describing wordcounts of individual parent/parent+child
        comments on a Post/ by a User.
        @param child_comments (bool): whether to parse child comments or not
        @param comment_votes (bool): whether to pass comment votes to self.word_weight,
                                    False passes 1 for all comments.
        @param comment_level (bool): whether to pass comment nest level to
                                    self.word_weight, False passes 1 for all comments.
        """
        if self._stype=='user' or self._stype=='post':
            CLASS = Post if self._stype=='post' else User
            temp = [CLASS('x', cs='x', cid='x', comments=[c]) for c in self.source.comments]
            for p in temp:
                p.word_weight = self.source.word_weight
                p.generate_word_counts(child_comments, comment_votes, comment_level)
            P = Parser(cid='asd', cs='asd', items=temp)
            P.consolidate()
            L = Learner(parser=P)
            L.get_eigenvectors()
            self.axes = L.axes
        else:
            raise Exception('get_comment_eigenvectors only for Post/User objects.')
