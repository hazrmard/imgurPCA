from __future__ import print_function
from __future__ import unicode_literals
from post import Post
from user import User
from parse import Parser
import utils
import config
import numpy as np
from csv import reader, writer


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
            # raise AttributeError('Include parser, post, or user key/value pair.')
            pass # for custom usage

        self.axes = None          # np.array 2D float [len(self.words) x # of axes]
        self._custom_words = None # list of words if custom axes set, alternative
                                  # to self.source.words. Set by self.set_axes()
        self.ccenters = None      # 2D array of cluster centers [arbitrary x # of axes]

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
        if self._custom_words is None:      # i.e. custom axes not set then:
            return self.source.wordcount['word']
        else:
            return self._custom_words


    def set_axes(self, axes, consolidated=False):
        """set custom axes for further computations. Overrides get_axes if
        used previously. Each axis is an array of words and their weights.
        @param axes (ndarray): a list/tuple/array/generator of config.DT_WORD_WEIGHT
                                arrays. Each array represents an axis.
        @param consolidated (bool): whether words and order in all axes is same.
        Returns 2D array (each row -> word weight in self.words, column -> axis vector)
        """
        if not consolidated:
            p = Parser(cs='bleh', cid='bleh')
            p.items = [Post(id='bleh', cid='bleh', cs='bleh', wordcount=w) for w in axes]
            p.consolidate()
            self._custom_words = p.words
            self.axes = np.vstack((a.wordcount['weight'] for a in p.items)).T
        else:
            self._custom_words = axes[0]['word']
            self.axes = np.vstack((a['weight'] for a in axes)).T
        return self.axes


    def get_axes(self):
        """get the eignevectors describing the wordcounts of the items in the
        Parser given to Learner. For comment-wise vectors, use get_comment_eigenvectors()
        Returns 2D array (each row -> word weight in self.words, column -> axis vector)
        """
        if self._stype=='parser':
            if self.source._consolidated:
                self._custom_words = None           # default to using source words
                counts = np.vstack((item.wordcount['weight'] for item in self.source.items)).T
                cov = np.cov(counts)
                eiw, eiv = np.linalg.eigh(cov)       # eiw=e-vals, eiv=e-vectors
                # Note .eig returns complex due to floating point precision errors
                order = eiw.argsort()[::-1]
                eiw = eiw[order]
                eiv = eiv[:, order]                 # vals/vecs ordered by largest eval
                self.axes = eiv
                return self.axes
            else:
                raise config.PrematureFunctionCall('Consolidate Parser first.')
        else:
            raise Exception('Use get_comment_axes for Post/User sources.')


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
        if self._stype=='user' or self._stype=='post':
            temp = [Post('x', cs='x', cid='x', comments=[c], points=1) for c in self.source.comments]
            for p in temp:
                p.word_weight = self.source.word_weight
                p.generate_word_counts(child_comments, comment_votes, comment_level)
            P = Parser(cid='asd', cs='asd', items=temp)
            P.consolidate()
            L = Learner(parser=P)
            self.axes = L.get_axes()
            self._custom_words = P.words    # since child_comments might be
                                            # different b/w source.generate_word_counts
                                            # and self.get_comment_axes
            return self.axes
        else:
            raise Exception('get_comment_axes only for Post/User objects.')


    def load_axes(self, fname):
        """load axes stored using save_axes()
        @param fname (str): name of file containing axes
        """
        n = utils.num_lines(fname)
        with open(fname, 'r') as f:
            c = reader(f)       # csv.reader
            words = c.next()
            self._custom_words = np.array(words, dtype=config.DT_WORD)['word']
            axes_t = np.zeros((n-1, len(words)), dtype=float)
            for i, row in enumerate(c):
                axes_t[i,:] = row
            self.axes = axes_t.T


    def save_axes(self, fname):
        """save the axes in a csv file. The first row is comma-separated self.words.
        The following rows correspond to axis vectors in self.axes (i.e. self.axes.T)
        @param fname (str): name of file to save
        """
        with open(fname, 'wb') as f:
            w = writer(f)
            w.writerow(self.words)
            w.writerows(self.axes.T)


    def project(self, source):
        """projects the wordcounts of the source on the axes calculated from the
        get_axes() or get_comment_axes() functions. If source is Parser, assumes
        that it is consolidated (for faster processing).
        @param source (Parser/Post/User): an instance of a Post/Parser/User object
                                        with wordcounts calculated.
        Returns a 2D numpy array of projections (each row->coordinates, column->axis)
        """
        if self.axes is None:
            raise config.PrematureFunctionCall('Calculate axes first.')
        wc = None
        if isinstance(source, Parser):
            if not source._consolidated:
                raise cofig.PrematureFunctionCall('Consolidate Parser first.')
            wc = (i.wordcount for i in source.items)
            weights = np.zeros((len(source.items), len(self.axes)))
        elif isinstance(source, User) or isinstance(source, Post):
            wc = [source.wordcount]
            weights = np.zeros((1,len(self.axes)))

        zero_words = np.setdiff1d(self.words, source.words, assume_unique=True)
        zero_wordcounts = np.array(zip(zero_words, np.zeros(len(zero_words))), dtype=config.DT_WORD_WEIGHT)
        in_both = np.in1d(source.words, self.words, assume_unique=True)
        for i, v in enumerate(wc):            # v-> vector , wc -> wordcount
            vec = np.append(v[in_both], zero_wordcounts)
            vec.sort(order=[config.DEFAULT_SORT_ORDER])
            # vec now only contains words present in self.words in same order
            weights[i] = vec['weight']
        return np.dot(weights, self.axes)   #projection = weights . axes


    def k_means_cluster(self, projections, nclusters):     # 'self' added by decorator
        """using projection coordinates, group coordinates together based on
        smallest cartesian distance to cluster centers.
        @param projections (2D ndarray): a 2D numpy array with rows representing
                                    coordinates on self.axes
        @param nclusters (int): number of clusters to create
        Returns a tuple. First element is a 2D numpy array with each row -> cluster
        center coordinate (len==# of axes).
        Second element is 1D numpy array the size of projection with int labels
        for each coordinate's cluster: [1,1,2,3,4,0....]. Numbers correspond to
        cluster indices in 1st element. Order corresponds to elements in
        projection argument.
        """
        pmax = np.amax(projections)  # get bounding box for cluster centers
        pmin = np.amin(projections)
        if len(projections.shape)==1:   # accounting for 1D projections if passed
            centers = np.random.randint(pmin, pmax, size=(nclusters, len(projections)))
        else:
            centers = np.random.randint(pmin, pmax, size=(nclusters, len(projections[0]))) # allocate memory
        pre = np.zeros(len(projections))
        nex = np.ones(len(projections))
        while not np.array_equal(pre, nex):
            pre = nex
            # calculate new assignments based on centers
            for i in range(len(projections)):
                closest = None
                for j in range(len(centers)):
                    diff = projections[i] - centers[j]
                    dist = np.dot(diff, diff)   # squared cartesian distance
                    if closest is None:
                        closest = dist
                        nex[i] = j
                    elif dist < closest:
                        closest = dist
                        nex[i] = j

            # calculate new centers based on assignments
            for k in range(len(centers)):
                mine = nex==k
                if np.any(mine):
                    centers[k] = np.mean(projections[mine], axis=0)

        self.ccenters = centers
        return centers, nex


    def assign_to_cluster(self, projections, ccenters=None):
        """given cluster center coordinates on self.axes, assign cluster to each
        projection based on the smallest cartesian distance.
        @param projections (ndarray): 2D numpy array of coordinates on self.axes.
        @param ccenters (ndarray): OPTIONAL. 2D numpy array of cluster center
                                coordinates. If not specified, result of k_means_cluster
                                is used.
        Returns a 1D array where each element is the index of cluster center in
        ccenters the projection matched with.
        """
        if ccenters is None:
            if self.ccenters is None:
                raise config.PrematureFunctionCall('Specify centers or call \
                            k_means_cluster first to compute centers.')
            ccenters = self.ccenters
        assignments = np.zeros(len(projections))
        for i in range(len(projections)):
            closest = None
            for j in range(len(ccenters)):
                diff = ccenters[j] - projections[i]
                dist = np.dot(diff, diff)
                if closest is not None:
                    if dist < closest:
                        assignments[i] = j
                        closest = dist
                else:
                    closest = dist
        return assignments


    def linear_regression(self, projections, predictions):
        """multiple linear regression. Fits projections and predictions on a plane
        using least squares fit.
        @param projections (ndarray): 2D numpy array of coordinates. Each row is
                                    one coordinate. Each column is an axis.
                                    [[x1, x2,...], [x1, x2,...],...]
        @param predictions (ndarray): 1D numpy array of predictions. [1 x predictions]
        Returns a 1D numpy array [1 + # of axes] corresponding to coefficients
        of the plane equation prediction = a0 + a1.x1 + a2.x2 +...
        """
        if len(projections.shape)==1:   # accounting for 1D projections if passed
            coefficients = np.vstack((np.ones(len(projections)), projections)).T
        else:
            coefficients = np.vstack((np.ones(projections.shape[0]), projections.T)).T
        return np.linalg.lstsq(coefficients, predictions)[0]
