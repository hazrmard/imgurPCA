# imgurpca.Parser
`Parser` is a collection of `User`/`Post` instances. It performs cumulative
feature selection operations and queries imgur for posts. `Parser` is
subclassed from `Molecular`.  

### Attributes
```
- items (list):
    A list of Post/User instances.

- nthreads (int):
    Number of threads to run downloads on in Parser.get(). Default=8.

- wordcount (ndarray):
    A numpy array of words and their weights. Of dtype=config.DT_WORD_WEIGHT.
    Each element has 2 fields: 'word' (32 char unicode) and 'weight' (float).
    Populated after consolidate().

- words (ndarray):
    A numpy array of words in wordcount. Same as Parser.wordcount['word']. Of
    dtype=config.DT_WORD. Read only.

- weights (ndarray):
    A numpy array of weights in wordcount. Same as Parser.wordcount['weight'].
    Of dtype=config.DT_WEIGHT. Read only.

- cs (str):
    The client secret. Set at instantiation if provided.

- cid (str):
    The client id. Set at instantiation if provided.

- client (ImgurClient):
    An instance of imgurpython.ImgurClient. Exposes entire imgurpython API.
```

### Instantiation
```python
def __init__(self, nthreads=8, *args, **kwargs):
# Example
from imgurpca import Parser
P = Parser(cs='client secret', cid='client id')
P = Parser(cs='client secret', cid='client id', items=[LIST_OF_POST_INSTANCES])
```
```
Parameters:
- nthreads (int):
    Number of threads to run downloads on in get(). Default=8.

- cid (string):
    Client ID, use with 'cs'.

- cs (string):
    Client secret, use with 'cid'.

OR:
- client (ImgurClient):
    imgurpython.ImgurClient instance. Use instead of 'cs' and 'cid'.

Any keyword arguments will be added as instance attributes.
```

### get
Query imgur for posts matching certain criteria. `get` takes a `Query` instance
as argument which provides a single interface to access various endpoints on
the imgur API.
```python
def get(self, query, pages=0):
# Example
from imgurpca import Query
q = Query(Query.GALLERY_HOT).sort_by(Query.TOP).over(Query.WEEK).construct()
P.get(q, pages=(0,2))
```
```
Parameters:
- query (Query):
    A Query instance which has construct() called on it.

- pages (int/tuple):
    Imgur responses for gallery items are paginated. Tuple specifies inclusive
    range of pages. Int specifies single page to download.
```

### download
To be called after `get()` or `populate_*()`. Runs on `Parser.nthreads` and
calls the `download()` function of User/Post instances.
```python
def download(self):
# Example
P.download()
```

### content
Returns a generator of (optionally flattened) comments for all objects in
`Parser.items`
```python
def content(self, flatten=True, accessor=lambda x:x.children):
# Example
g = P.content(flatten=False)    # only top level comments
```
```
Parameters
- flatten (bool):
    Whether to include child comments or  not.
```

### populate_posts
Instantiates `Post` objects from post ids or Imgur Gallery Image/Album/
GalleryAlbum objects. Instances are placed in self.items.
```python
def populate_posts(self, posts):
# Example
P.populate_posts(['id1', 'id2', 'id3'])
```
```
Parameters:
- posts (list):
    A list of post ids (str) or Gallery Image/Album/GalleryAlbum objects.
```

### populate_users
Instantiates `User` objects from usernames or Account objects. Instances are
placed in self.items.
```python
def populate_users(self, users):
# Example
P.populate_users(['id1', 'id2', 'id3'])
```
```
Parameters:
- users (list):
    A list of usernames (str) or Account objects. See imgur API data models.
```

### consolidate
Gives each object in `Parser.items` the same set and order of words in their
`wordcount`. Sorts cumulative wordlist and item wordlists (by word) so index
positions are identical.This makes the data set homogenous. This also populates
`Parser.wordcount`. Consolidate should be called after `Parser.items`'s
wordcounts have been generated.
```python
def consolidate(self, words=None):
# Example
P.consolidate()
P.consolidate(words=['my', 'name'])     # only keep words 'my' and 'name'
```
```
Parameters:
- words (list/ndarray):
    A list of words (str) to keep. If words are not present in items' words,
    they will be added with 0 weights.
```

### get_baseline
Calculate means and variances of words in `Parser.items`'s wordcounts. This
can then be used to filter out frequent or consistently appearing words to
reduce bloat. Can only be called after consolidation.
```python
def get_baseline(self):
# Example
P.get_baseline()
```
```
Parameters:
Returns a tuple -> (average weights, variances) of 1D np arrays where order
corresponds to self.words.
```

### split
Splits instances in `Parser.items` into two parts to be used as training and
testing data sets.  
NOTE: items returned are references to self.items. So any changes to items in
self.items or in the 2 returned collections will be reflected.
```python
def split(self, fraction=0.5):
# Example
P.split(0.3)        # 30%-70% split
```
```
Parameters:
- fraction (float):
    Fraction of items to keep in first of 2 lists.

Returns 2 lists of Post/User instances.
```
