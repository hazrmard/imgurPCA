from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from imgurpca.base import BaseLearner
from imgurpca.base import Atomic
from imgurpca import Post
from imgurpca import Parser
from csv import reader, writer


class Learner(BaseLearner):

    def __init__(self, *args, **kwargs):
        """provide a source as a keyword argument
        @param source (Parser/User/Post): a an instance of Atomic/Molecular subclass
        """
        super(Learner, self).__init__(**kwargs)


    def get_comment_axes(self, child_comments=False, comment_votes=True,
                            comment_level=True):
        """get eigenvectors describing wordcounts of individual parent/parent+child
        comments on a Post/ by a User.
        @param child_comments (bool): whether to parse child comments or not
        @param comment_votes (bool): whether to pass comment votes to self.word_weight,
                                    False passes 1 for all comments.
        @param comment_level (bool): whether to pass comment nest level to
                                    self.word_weight, False passes 1 for all comments.
        Returns and sets self.axes (2D array) as the principal components (column -> axis)
        """
        if isinstance(self.source, Atomic):
            temp = [Post('x', cs='x', cid='x', comments=[c], points=1) for c in self.source.comments]
            for p in temp:
                p.word_weight = self.source.word_weight
                p.generate_word_counts(child_comments, comment_votes, comment_level)
            P = Parser(cid='asd', cs='asd', items=temp)
            P.consolidate()
            L = Learner(source=P)
            self.axes = L.get_axes()
            self._custom_words = P.words    # since child_comments might be
                                            # different b/w source.generate_word_counts
                                            # and self.get_comment_axes
            return self.axes
        else:
            raise Exception('get_comment_axes only for Post/User objects.')
