# imgurpca.Learner
`Learner` provides various analytical functions to conduct supervised and
unsupervised learning.

### Attributes
```
- source (Parser/User/Post):
    Either one of Parser/User/Post instances. If User/Post, should have
    wordcounts generated. If parser, should be consolidated.

- axes (2D ndarray):
    A 2 dimensional numpy array where each column represents an axis vector.
    Each row represents weight for words in Learner.words.

- words (ndarray):
    An array of words in the source's wordcount. Axis weights for words are
    in this order.

- ccenters (2D ndarray):
    A 2D numpy array of cluster center coordinates on Learner.axes. Populated
    after Learner.k_means_cluster(). Each row is the coordinates of a center.

- lrc (ndarray):
    An array of linear regression coefficients. 'a' in a0 + a1.x1 + a2.x2
    +..., where (x1, x2...) represent axis coordinates.

- lrf (func):
    A logistic regression function. Maps a 2D array of coordinates to an array
    of binary labels.

- dtree (DTree):
    An instance of base.DTree representing a decision tree. Populated after
    decision_tree() is called.
```

### Instantiation
```python
def __init__(self, source, *args, **kwargs):
# Example
from imgurpca import Learner
L = Learner(source=SOME_PARSER)
```
```
Parameters:
- source (Parser/Post/User):
    An instance of a consolidated parser, or a Post/User with wordcounts
    generated.
```

### get_axes
Use the item wordcounts in parser to generate axes that best describe the
differences in `Parser.items`. Essentially, takes the eigenvectors of the
covariance matrix of wordcounts in parser's items. The eigenvectors are
sorted in descending order and stored in `Learner.axes`.
```python
def get_axes(self):
# Example
L.get_axes()
```

### get_comment_axes
Use the comments separately in Post/User source to generate axes that best
describe differences in comments. Same as `get_axes()` but at a comment
level and for a single Post/User.
```python
L = Learner(source=SOME_USER)
L.get_comment_axes()
```

### set_axes
Set custom axes.
```python
def set_axes(self, axes, consolidated=False):
# Example
from imgurpca import config
import numpy as np

ax1 = np.array([('my',0.5), ('name', 0.9)], dtype=config.DT_WORD_WEIGHT)
ax2 = np.array([('my',1.0), ('name', 0.0)], dtype=config.DT_WORD_WEIGHT)
ax3 = np.array([('my',0.5), ('is', 0.4)], dtype=config.DT_WORD_WEIGHT)

L.set_axes([ax1, ax2], consolidated=True)         # uniform words
L.set_axes([ax1, ax2, ax3], consolidated=False)   # non-uniform words
```
```
Parameters:
- axes (2D ndarray/ list of ndarray):
    A 2D array or a list of numpy arrays of dtype=config.DT_WORD_WEIGHT

- consolidated (bool):
    Whether all axis have the same words in the same order. If true, speeds
    up computation.
```

### save_axes
Save axes to a csv file for later use.
```python
def save_axes(self, fname):
# Example
L.save_axes('test.csv')
```
```
Parameters:
- fname (str):
    Name of file to store axes in.
```

### load_axes
Load axes from a csv file. Must be the same format that `save_axes()` used.
```python
def load_axes(self, fname):
# Example
L.load_axes('test.csv')
```
```
Parameters:
- fname (str):
    Name of file to load axes from.
```

### project
Project a Post/User or items in `Parser.items` onto `Learner.axes`.
```python
def project(self, source):
# Example
proj = L.project(SOME_USER)     # user must have wordcounts generated
proj = L.project(SOME_PARSER)   # parser items must have wordcounts generated
```
```
Parameters:
- source (Parser/User/Post):
    A Parser or User/Post instance with wordcounts generated.

Returns a 2D ndarray where each row is the projection onto self.axes.
```

### k_means_cluster
Using projection coordinates, group coordinates together based on smallest
Cartesian distance to cluster centers.
```python
def k_means_cluster(self, projections, nclusters):
# Example
ccenters, assignments = L.k_means_cluster(proj, 3)
```
```
Parameters:
- projections (2D ndarray):
    A 2D array of projections where each row contains coordinates for an
    item on Learner.axes. For 1D array each element is a separate coordinate.

- nclusters (int):
    Number of clusters to create. Clusters are generated randomly and then
    converge to the final value.

Returns a tuple of 2 arrays:
First element is a 2D numpy array with each row -> cluster center coordinate.
Second element is 1D numpy array the size of projection with int labels
for each coordinate's cluster: [1,1,2,3,4,0....]. Numbers correspond to
cluster indices in 1st element.
```

### assign_to_cluster
Given cluster center coordinates and projections, compute which projection
belongs to which cluster using smallest Cartesian distance. By default, uses
centers computed in `k_means_cluster()`.
```python
def assign_to_cluster(self, projections, ccenters=None):
# Example
assignments = L.assign_to_cluster(np.array([[1,2], [3,4]]))
```
```
Parameters:
- projections (2D ndarray):
    A 2D array of projections where each row contains coordinates for an
    item on Learner.axes. For 1D array each element is a separate coordinate.

- ccenters (2D ndarray):
    A 2D numpy array with each row -> cluster center coordinate. If none,
    self.ccenters is used (assuming k_means_cluster() has been called).

Returns an array the same length as projections containing indices to
ccenters to which projections belong.
```

### linear_regression
Multiple linear regression. Fits projections and predictions on a plane
using least squares fit.
```python
def linear_regression(self, projections, predictions, store=True):
# Example
proj = np.array([[1,2],[3,4],[5,6]])    # 3 projections
pred = np.array([3,7,11])               # 3 predictions
coeff = L.linear_regression(proj, pred)
```
```
Parameters:
- projections (2D ndarray):
    A 2D array of projections where each row contains coordinates for an
    item on Learner.axes. For 1D array each element is a separate coordinate.

- predictions (ndarray):
    A 1D array of predictions for each of the projections in the same order.

Returns an array of linear regression coefficients. 'a' in y = a0 + a1.x1 +
a2.x2 +..., where (x1, x2...) represent projection and y is prediction.
```

### linear_prediction
Given linear regression coefficients, calculate the predictions based
on the projections.
```python
def linear_prediction(self, projections, coefficients=None):
# Example
proj = L.project(SOME_OTHER_PARSER)
pred = L.linear_prediction(proj)
```
```
Parameters:
- projections (2D ndarray):
    A 2D array of projections where each row contains coordinates for an
    item on Learner.axes. For 1D array each element is a separate coordinate.

- coefficients (ndarray):
    1D array of linear regression coefficients. Defaults to self.lrc after
    linear_regression() is called.

Returns a 1D array of predictions in the same order as projections.
```

### logistic_regression
Performs logistic regression on projections and their binary labels. Logistic
regression is a way of classifying data that have one of 2 labels (0 or 1).
```python
def logistic_regression(self, projections, labels):
# Example
proj = L.project(SOME_OTHER_PARSER)
pred = np.array([1 if p.title[:3]=='MRW' else 0 for p in A_PARSER.items])
pred_func = L.logistic_regression(proj, pred)
```
```
Parameters:
- projections (2D ndarray):
    A 2D array of projections where each row contains coordinates for an
    item on Learner.axes. For 1D array each element is a separate coordinate.

- labels (ndarray):
    A 1D numpy array of binary labels (0/1) for each projection.

Returns a function that when passed a projection[s] gives a binary label.
```

### logistic_prediction
Compute the labels for each projection based on a logistic regression
function.
```python
def logistic_prediction(self, projections, rfunc=None):
# Example
proj = L.project(SOME_OTHER_PARSER)
new_pred = L.logistic_prediction(proj)
```
```
Parameters:
- projections (2D ndarray):
    A 2D array of projections where each row contains coordinates for an
    item on Learner.axes. For 1D array each element is a separate coordinate.

- rfunc (func):
    A function that takes a single projection and returns a label. Defaults
    to the function calculated in logistic_regression()

Returns a 1D array of binary labels the same length as projections.
```

### decision_tree
Constructs a decision tree, given the data set, labels, and number of branches
or splitting points. A decision tree splits data by the attribute which causes
the greatest information gain (pre-split entropy - post-split entropy). It
keeps splitting until there are no more attributes or if all data are
classified.
```python
def decision_tree(self, projections, labels, branches=2):
# Example
proj = np.array([[1,1,0],[1,1,1],[0,0,0],[0,0,1]])
labels = np.array([0,1,0,1])
dtree = L.decision_tree(proj, labels, branches=2)   # all attributes split in 2
dtree = L.decision_tree(proj, labels, branches=[2,3,4])  # 1st attr: 2 branches,
                                                         # 2nd attr: 3 branches,
                                                         # 3rd attr: 4 branches.
dtree = L.decision_tree(proj, labels,
                        branches=np.array([[0.5],   # 1st attr splits at 0.5
                                           [0.33,0.66], # splits at 0.33 & 0.66
                                           [0.25,0.50,0.75]]))  # splits @ 3 pts
```
```
Parameters:
- projections (2D ndarray):
    A 2D array of projections where each row contains coordinates for an
    item on Learner.axes. For 1D array each element is a separate coordinate.

- labels  (ndarray):
    A 1D numpy array of numerical labels for each projection.

- branches (int/array/2D array):
    Specifies number of branches on each attribute. If int, same number of
    branches for all attributes. If list, each element inside is the # of
    branches for attribute in that index in coordinates. If list of lists, each
    sub-list specifies the values at which to split an attribute. Values are
    upper bounds (inclusive) of the split. For n values, there will be n+1
    splits. A minimum of n=1 (split points) i.e 2 branches are required
    for all attributes. If no split points provided or branches=1 for an
    attribute, it is ignored.

Returns a base.DTree instance which represents the decision tree. The instance
has 2 useful methods:
    - print_tree(): prints the various branches of the tree for visualization,
    - classify():   given a 2D array of projections, computes probable labels
                    for each. Use Learner.decision_prediction() instead.
```

### decision_prediction
After the decision tree is computed, calculates probabilities of each label for
each projection provided. So a projection may have a 75% chance of being
labelled 1 and a 25% chance of being labelled 2.
```python
def decision_prediction(self, projections):
# Example
proj = np.array([[1,0,1],[1,1,0]])
res = L.decision_prediction(proj)
```
```
Parameters:
- projections (2D ndarray):
    A 2D array of projections where each row contains coordinates for an
    item on Learner.axes. For 1D array each element is a separate coordinate.

Returns a 3D numpy array. The first axis is an array of 2D predictions for each
projection. Each prediction is a 2D array where each row is of the form [label,
probability of being that label].
```
