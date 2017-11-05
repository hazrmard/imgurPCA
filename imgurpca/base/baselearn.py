from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
from . import Atomic
from . import Molecular
from . import DTree
from . import utils
from . import config
import numpy as np
from csv import reader, writer
from collections import deque

# BaseLearner provides functions that generate axes to describe data points and
# perform further analyses. Axes are generated from the source which is a Molecular
# subclass. They can also be saved to and loaded from file, or set programmatically.
# The class does principal component analysis, linear and logistic regression and
# prediction, and k-means clustering.

class BaseLearner(object):

    def __init__(self, source=None, *args, **kwargs):
        """provide a source as a keyword argument
        @param source (Atomic/Molecular): a an instance of Atomic/Molecular subclass
        """
        self.source = source
        self.axes = None          # np.array 2D float [len(self.words) x # of axes]
        self._custom_words = None # list of words if custom axes set, alternative
                                  # to self.source.words. Set by self.set_axes()
        self.ccenters = None      # 2D array of cluster centers [arbitrary x # of axes]
        self.lrc = None           # linear regression coefficients 1D array of a's in:
                                  # a0 + a1.x1 + a2.x2+...
        self.lrf = None           # logistic regression function, result of
                                  # Learner.logistic_regression()
        self.dtree = None         # base.DTree instance after decision_tree() is
                                  # called. Used for prediction.

        for attr in kwargs:
            setattr(self, attr, kwargs[attr])

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
            p = Molecular()
            p.items = [Atomic(wordcount=w) for w in axes]
            p.consolidate()
            self._custom_words = p.words
            self.axes = np.vstack((a.wordcount['weight'] for a in p.items)).T
        else:
            self._custom_words = axes[0]['word']
            self.axes = np.vstack((a['weight'] for a in axes)).T
        return self.axes


    def get_axes(self, n=-1):
        """get the eignevectors describing the wordcounts of the items in the
        Molecular given to Learner. For comment-wise vectors, use get_comment_eigenvectors()
        Returns 2D array (each row -> word weight in self.words, column -> axis vector)
        @param n (int): Number of axes to get. Defaults to all eigenvectors.
        """
        if isinstance(self.source, Molecular):
            if self.source._consolidated:
                self._custom_words = None           # default to using source words
                counts = np.vstack((item.wordcount['weight'] for item in self.source.items))
                counts = counts - np.mean(counts, axis=0)
                cov = np.cov(counts.T)
                eiw, eiv = np.linalg.eigh(cov)       # eiw=e-vals, eiv=e-vectors
                # Note .eig returns complex due to floating point precision errors
                order = eiw.argsort()[::-1]
                eiw = eiw[order]
                eiv = eiv[:, order]                 # vals/vecs ordered by largest eval
                if n==-1:
                    self.axes = eiv
                else:
                    self.axes = eiv[:, :n]
                return self.axes
            else:
                raise config.PrematureFunctionCall('Consolidate first.')
        else:
            raise Exception('Does not work on Atomic objects.')


    def load_axes(self, fname):
        """load axes stored using save_axes()
        @param fname (str): name of file containing axes
        """
        n = utils.num_lines(fname)
        with open(fname, 'r', newline='') as f:
            c = reader(f)       # csv.reader
            words = next(c)
            self._custom_words = np.array(list(zip(words)), dtype=config.DT_WORD)['word']   # must me a list of tuples for structured array creation
            axes_t = np.zeros((n-1, len(words)), dtype=float)
            for i, row in enumerate(c):
                axes_t[i,:] = row
            self.axes = axes_t.T


    def save_axes(self, fname):
        """save the axes in a csv file. The first row is comma-separated self.words.
        The following rows correspond to axis vectors in self.axes (i.e. self.axes.T)
        @param fname (str): name of file to save
        """
        with open(fname, 'w', newline='') as f:
            w = writer(f)
            w.writerow(self.words)
            w.writerows(self.axes.T)


    def project(self, source):
        """projects the wordcounts of the source on the axes calculated from the
        get_axes() or get_comment_axes() functions. If source is Molecular, assumes
        that it is consolidated (for faster processing).
        @param source (Atomic/Molecular): an instance of an Atomic/Molecular object
                                        with wordcounts calculated.
        Returns a 2D numpy array of projections (each row->coordinates, column->axis)
        """
        # PREPROCESSING
        if self.axes is None:
            raise config.PrematureFunctionCall('Calculate axes first.')
        wc = None
        if isinstance(source, Molecular):
            if not source._consolidated:
                raise cofig.PrematureFunctionCall('Consolidate first.')
            wc = (i.wordcount for i in source.items)
            weights = np.zeros((len(source.items), len(self.axes)))
        elif isinstance(source, Atomic):
            wc = [source.wordcount]
            weights = np.zeros((1,len(self.axes)))
        # CALCULATIONS
        zero_words = np.setdiff1d(self.words, source.words, assume_unique=True)
        zero_wordcounts = np.array(list(zip(zero_words, np.zeros(len(zero_words)))), dtype=config.DT_WORD_WEIGHT)
        in_both = np.in1d(source.words, self.words, assume_unique=True)
        for i, v in enumerate(wc):            # v-> vector , wc -> wordcount
            vec = np.append(v[in_both], zero_wordcounts)
            vec.sort(order=[config.DEFAULT_SORT_ORDER])
            # vec now only contains words present in self.words in same order
            weights[i] = vec['weight']
        return np.dot(weights, self.axes)   #projection = weights . axes


    def k_means_cluster(self, projections, nclusters):
        """using projection coordinates, group coordinates together based on
        smallest cartesian distance to cluster centers.
        @param projections (2D ndarray): a 2D numpy array with rows representing
                                    coordinates on self.axes. If 1D array, each
                                    element is considered a separate coordinate.
        @param nclusters (int): number of clusters to create
        Returns a tuple. First element is a 2D numpy array with each row -> cluster
        center coordinate (len==# of axes).
        Second element is 1D numpy array the size of projection with int labels
        for each coordinate's cluster: [1,1,2,3,4,0....]. Numbers correspond to
        cluster indices in 1st element. Order corresponds to elements in
        projection argument.
        """
        # PREPROCESSING
        if isinstance(projections, (int, float)):
            proj = np.array([proj])
        if len(projections.shape)==1:   # accounting for 1D projections if passed
            projections = projections.reshape((1,-1)).T
        # CALCULATIONS
        pmax = np.amax(projections)  # get bounding box for cluster centers
        pmin = np.amin(projections)
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
                                    If 1D, each element is a separate coordinate.
        @param ccenters (ndarray): OPTIONAL. 2D numpy array of cluster center
                                coordinates. If not specified, result of k_means_cluster
                                is used.
        Returns a 1D array where each element is the index of cluster center in
        ccenters the projection matched with.
        """
        # PREPROCESSING
        if ccenters is None:
            if self.ccenters is None:
                raise config.PrematureFunctionCall('Specify centers or call \
                            k_means_cluster first to compute centers.')
            ccenters = self.ccenters
        if isinstance(projections, (int, float)):
            proj = np.array([proj])
        if len(projections.shape)==1:
            projections = projections.reshape((1,-1))
        # CALCULATIONS
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


    def linear_regression(self, projections, predictions, store=True):
        """multiple linear regression. Fits projections and predictions on a plane
        using least squares fit.
        @param projections (ndarray): 2D numpy array of coordinates. Each row is
                                    one coordinate. Each column is an axis.
                                    [[x1, x2,...], [x1, x2,...],...]
                                    If 1D, each element is a separate coordinate.
        @param predictions (ndarray): 1D numpy array of predictions. [1 x predictions]
        @param store (bool): whether to store results in self.lrc for later use.
        Returns a 1D numpy array [1 + # of axes] corresponding to coefficients
        of the plane equation prediction = a0 + a1.x1 + a2.x2 +...
        """
        # PREPROCESSING
        if isinstance(projections, (int, float)):
            proj = np.array([proj])
        if len(projections.shape)==1:   # accounting for 1D projections if passed
            projections = projections.reshape((1,-1)).T
        coefficients = np.vstack((np.ones(projections.shape[0]), projections.T)).T
        # CALCULATIONS
        res =  np.linalg.lstsq(coefficients, predictions)[0]
        if store:
            self.lrc = res
        return res


    def linear_prediction(self, projections, coefficients=None):
        """given linear regression coefficients, calculate the predictions based
        on the projections.
        @param projections (ndarray): a 2D numpy array of n coordinates [n x dimensions].
                                    If 1D, each element is a separate coordinate.
        @param coeffieients (ndarray): OPTIONAL. a 1D array of dimensions+1 coeffienents:
                                    [a0, a1, a2,...], a0 is intercept/bias
        Returns a 1D array of predictions in the same order as projections.
        """
        # PREPROCESSING
        if coefficients is None:
            if self.lrc is None:
                raise config.PrematureFunctionCall('Specify coefficients of \
                                call linear_regression() first.')
            coefficients = self.lrc
        if isinstance(projections, (int, float)):
            proj = np.array([proj])
        if len(projections.shape)==1:
            projections = projections.reshape((1,-1)).T
        # CALCULATIONS
        return coefficients[0] + np.dot(coefficients[1:], projections.T)


    def logistic_regression(self, projections, labels):
        """perform logistic regression on projections and their binary labels.
        @param projections (ndarray): a 2D numpy array of n coordinates [n x dimensions].
                                    If 1D, each element is a separate coordinate.
        @param labels (ndarray): a 1D numpy array of n 0/1 labels for each projection.
        Returns a function that when passed a single projection (1D array) returns
        a 1 or 0 label.
        """
        c = self.linear_regression(projections, labels, False)  # coefficients
        def r(proj):    # proj is a 1D array of a single coordinate
            if isinstance(proj, (int, float)):
                proj = np.array([proj])
            y = c[0] + np.dot(proj, c[1:])
            z = 1 / (1 + np.exp(-y))
            return 1 if z>=0.5 else 0
        self.lrf = r
        return r


    def logistic_prediction(self, projections, rfunc=None):
        """compute the labels for each projection based on logistic regression
        function.
        @param projections (ndarray): a 2D numpy array of n coordinates [n x dimensions].
                                    If 1D, each element is a separate coordinate.
        @param rfunc (function): OPTIONAL. a function that takes a single element
                                in projections and returns a label.
        Returns a 1D numpy array of binary labels in the same order as projections.
        """
        # PREPROCESSING
        if rfunc is None:
            if self.lrf is None:
                raise config.PrematureFunctionCall('Specify rfunc or call linear\
                            _regression() first.')
            rfunc = self.lrf
        if isinstance(projections, (int, float)):
            proj = np.array([proj])
        if len(projections.shape)==1:
            projections = projections.reshape((1,-1)).T
        labels = np.zeros(len(projections))
        # CALCULATIONS
        for i in range(len(labels)):
            labels[i] = rfunc(projections[i])
        return labels


    def decision_tree(self, projections, labels, branches=2):
        """computes a decision tree based on attributes contained in projections
        by splitting by attribute which yields maximum information gain for the
        labels. Splits until all coordinates in projections used up or if there
        is no entropy in the label subsets.
        @param projections (ndarray): a 2D numpy array where each row is
                            coordinates representing a point. If 1D, each element
                            is considered a separate coordinate of 1 dimension.
        @param labels (list/array): a list of numerical labels for each of the
                            coordinates in projections.
        @branches (int/array/2D array): specifies number of branches on each
                            attribute. If int, same number of branches for
                            all attributes. If list, each element inside is
                            the # of branches for attribute in that index in
                            coordinates. If list of lists, each sublist specifies
                            the values at which to split an attribute. Values
                            are upper bounds (inclusive) of the split. For
                            n values, there will be n+1 splits. A minimum of
                            n=1 (split points) i.e 2 branches are required
                            for all attributes.
        """
        # PREPROCESSING
        if len(projections.shape)==1:
            projections = projections.reshape((1,-1)).T
        if isinstance(branches, (int, float)):      # if branches is number, conv to list of #
            branches = [branches] * len(projections[0])
        if isinstance(branches, (list, tuple, np.ndarray)) and \
            isinstance(branches[0], (int, float)):  # if list of #, conv to list of
            nbranches = []                          # lists of split points
            for i, n in enumerate(branches):
                minimum = np.min(projections[:, i])             # smallest value of attribute
                d = (np.max(projections[:, 1]) - minimum) / n   # interval between branch values
                nbranches.append([minimum+j*d for j in range(1,n)])
            branches = nbranches
        branches = np.array(branches)
        # Now branches is a 2D array, where each sublist contains the
        # inclusive top limit of splits for each attribute
        # i.e [[1,2],[2,3]...], then the first sublist, [1,2] containing 2 values,
        # for the first attribute [<=1, >1 and <=2, >2] will split projections
        # into 2+1 branches
        # CALCULATIONS
        dtree = DTree()                       # contains the finished decision tree
        counter=0                             # counts # of nodes added to tree
        q = deque()                           # contains references to proj pending _find_max_info_gain
        bfilter = np.array([1 if len(x) else 0 for x in branches], dtype=bool)
        q.appendleft((np.ones(len(labels), dtype=bool), 0, -1, bfilter)) # queue of (filter, index, parent, branch_filter)

        while len(q):                         # breadth-first traversal of decision tree
            f, index, parent, bfilter = q.pop()
            ig, bi, filters, probs = self._find_max_info_gain(projections[f][:,bfilter], labels[f], branches[bfilter])

            if bi is not None:
                j=0                             # bi is the index of branch axis in
                for i, b in enumerate(bfilter): # branches[bfilter], i.e. the bi'th
                    if b:                       # True value in bfilter. This finds
                        j+=1                    # the absolute index of that True
                        if i==bi:               # value, hence branch axis in the
                            break               # original array 'branches'.

            dtree.add_node(index=index, parent=parent, axis=i if bi is not None else None,
                    branch=branches[bi] if bi is not None else (), probabilities=probs)

            bfilter_copy = np.copy(bfilter)
            bfilter_copy[bi] = False
            if ig>0:    # if there was any info gain, then process results
                for fi in filters:          # fi is of length f[f], i.e. whatever the
                    counter+=1              # filter let through, so cannot apply to
                    f_copy = np.copy(f)     # the original projections. This resizes
                    f_copy[f_copy] = fi[:]  # fi so it can directly act on projections.
                    q.appendleft((f_copy, counter, index, bfilter_copy))
            else:       # if no info gain i.e no more branches or labels fully classified
                pass
        dtree.construct()
        self.dtree = dtree
        return self.dtree


    def decision_prediction(self, projections):
        """given projections, outputs an array of prorabilities for each label
        that each projection might belong to.
        @param projections (2D ndarray): a 2D array, where each row is a
                        coordinate. If 1D each element is a separate coordinate.
        Returns a 3D numpy array. The first axis is an array of 2D predictions
        for each projection. Each prediction is a 2D array where each row is
        of the form [label, probability of being that label].
        """
        if len(projections.shape)==1:
            projections = projections.reshape((1,-1)).T
        return self.dtree.classify(projections)


    def _find_max_info_gain(self, projections, labels, branches):
        """given projections, their labels, and branching points, calculates
        branching on which attribute would yeild the maximum information gain.
        @param projections (ndarray): 2D numpy array, each row-> coordinate.
        @param labels (array/list): list of labels same length as projections.
        @param branches (ndarray/list): 2D array, each row -> split points for
                                    coord attribute/axis in the row's index.
        Returns a tuple of:    (maximum info gain,
                                index of axis that was split,
                                bool filters describing projs in each split,
                                an array of tulples (label, probability))
        """
        mig_bi = None   # max information gain branch index
        mig = 0         # max info gain
        mig_f = None    # max info gain filters

        ulbl, counts = np.unique(labels, return_counts=True)
        size_parent = len(labels)
        p = counts / size_parent       # probability p
        entropy_parent = np.sum(-p * np.log(p))
        labels_probs = np.vstack((ulbl, p)).T

        for i, b in enumerate(branches):    # find which attribute's branching -> max info
            if not len(b):
                continue        # do not process when no branching -> no info gain
            filters = self._split(projections, b, i)
            entropy_children = 0
            for f in filters:   # for each branch split, compute its contribution to entropy
                if not np.any(f):
                    continue    # skip if filter all false
                filtered_labels = labels[f]
                filtered_labels_sz = len(filtered_labels)
                _, ccounts = np.unique(filtered_labels, return_counts=True)
                cp = ccounts / filtered_labels_sz     # child probability
                entropy_children += np.sum(-cp * np.log(cp)) * filtered_labels_sz / size_parent
            ig = entropy_parent - entropy_children    # information gain
            if ig>mig:
                mig = ig
                mig_bi = i
                mig_f = filters

        return mig, mig_bi, mig_f, labels_probs


    def _split(self, projections, branch, index):
        """returns boolean arrays that act as filters on projections and labels
        to split them according to breakpoints in branch.
        @param projections (ndarray): 2D ndarray, each row is a coordinate.
        @param branch (list/array): a list of n values to split into n+1 branches.
        @param index (int): index of attribute in coordinate the branch applies to.
        Returns a list of boolean arrays, each array filtering in indices belonging
        to its branch.
        """
        if len(branch):
            cond = []
            for b in branch:
                cond.append(projections[:,index]<=b)
            cond.append(projections[:,index]>branch[-1])
        else:
            cond = [np.zeros(len(projections), dtype=bool)]
        return np.array(cond)
