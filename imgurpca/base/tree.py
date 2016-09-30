from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
import numpy as np

# The class DTree is a representation of a decision tree. Each node has the
# index of the coordinate axis to branch on, branching points (for n+1 branches),
# references to child nodes, and probabilities of each label until that node.
# A single Node represents a point of branching in the decision tree.


class Node(object):

    def __init__(self, **kwargs):
        self.parent = None          # index of parent node, -1 for root
        self.children = []          # list of node objects
        self.branch = None          # branching points
        self.axis = None            # axis index to apply branch on
        self.probabilities = None   # probs for each label at that node
        for attr in kwargs:
            setattr(self, attr, kwargs[attr])


class DTree:

    def __init__(self, *args, **kwargs):
        self._content = []

        for attr in kwargs:
            setattr(self, attr, kwargs[attr])

    @property
    def root(self):
        return self._content[0]


    def add_node(self, **kwargs):
        """adds a node to be processed into a tree. kwargs must contain 'index',
        'parent' keywords to identify each node. Additional keywords are
        decision tree specific parameters.
        @param index (int): The position of node if tree is counted in a breadth
        first manner. Root has index 0.
        @param parent (int): Index of the node that current node is descended
        from. Root has parent -1.
        """
        self._content.append(Node(**kwargs))


    def construct(self):
        """after nodes have been added, constructs a tree. To be called after
        all insertions are finished.
        """
        self._content.sort(key=lambda x: (x.parent, x.index))
        i=0
        j=1
        while i<len(self._content):
            while j<len(self._content):
                if self._content[j].parent == self._content[i].index:
                    self._content[i].children.append(self._content[j])
                    j+=1
                else:
                    break
            i+=1


    def classify(self, projections):
        """given projections, outputs an array of prorabilities for each label
        that each projection might belong to.
        @param projections (2D ndarray): a 2D array, where each row is a
                        coordinate.
        Returns a 3D numpy array. The first axis is an array of 2D predictions
        for each projection. Each prediction is a 2D array where each row is
        of the form [label, probability of being that label].
        """
        res = []
        for proj in projections:
            n = self.root
            while len(n.children):
                found = False
                for i, b in enumerate(n.branch):
                    if proj[n.axis] <= b:
                        n = n.children[i]
                        found = True
                if not found:
                    if len(n.branch)+1==len(n.children):
                        n = n.children[-1]
                    else:
                        break
            res.append(n.probabilities)
        return np.array(res)


    def print_tree(self):
        """given a constructed decision tree, use depth-first search to print
        conditions and final labels.
        """
        stack = [(self.root, 0, 0)]     # (node, child no., tabs)
        ntabs = 0
        while len(stack):
            n, i, tabs = stack.pop()
            if len(n.branch):
                if i>=1 and i==len(n.children)-1:
                    print(tabs*'\t' + 'axis-' + str(n.axis) + ': >' + str(n.branch[i-1]))
                else:
                    print(tabs*'\t' + 'axis-' + str(n.axis) + ': <=' + str(n.branch[i]))
                    stack.append((n, i+1, tabs))
                if i<len(n.children):
                    stack.append((n.children[i], 0, tabs+1))
            else:
                avg = np.dot(n.probabilities[:,0], n.probabilities[:,1])
                print(tabs*'\t' + 'Label: ' + str(avg) + '\n')
