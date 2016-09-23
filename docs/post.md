# imgurpca.Post
`Post` represents a single post's comments on imgur. It is subclassed from
`Atomic`.

### Attributes
```
- id (str):
    The post id used by imgur.

- points (int):
    Points accumulated by post.

- comments (list):
    A list of comment objects (see imgur API data models) associated with the
    post.

- content (list):
    An alias for comments. Read only.

- user (account):
    An account object for the post author (see imgur API data models).

- network (list):
    A list of user ids (str) associated with the post.  Alias for
    Post.get_user_ids. Read only.

- wordcount (ndarray):
    A numpy array of words and their weights. Of dtype=config.DT_WORD_WEIGHT.
    Each element has 2 fields: 'word' (10 char unicode) and 'weight' (float).
    Populated after generate_word_counts().

- words (ndarray):
    A numpy array of words in wordcount. Same as Post.wordcount['word']. Of
    dtype=config.DT_WORD. Read only.

- weights (ndarray):
    A numpy array of weights in wordcount. Same as Post.wordcount['weight']. Of
    dtype=config.DT_WEIGHT. Read only.

- word_weight (func):
    A function object that takes three arguments: post points, comment vote,
    and comment level. Used by generate_word_counts(). Defaults to
    config.DEFAULT_WORD_WEIGHT.

- cs (str):
    The client secret. Set at instantiation.

- cid (str):
    The client id. Set at instantiation.

- client (ImgurClient):
    An instance of imgurpython.ImgurClient. Exposes entire imgurpython API.

In addition, after download() is called attributes in the 'Gallery Image/Album'
data model are also assigned to the instance. See imgur API data models for
details.
```

### Instantiation
```python
def __init__(self, id, **kwargs):
# Example
from imgurpca import Post
u = Post('axvw', cs='my client secret', cid='my client id')
```
```
Parameters:
- id (str):
    The post ID.

- cid (string):
    Client ID, use with 'cs'.

- cs (string):
    Client secret, use with 'cid'.

OR:
- client (ImgurClient):
    imgurpython.ImgurClient instance. Use instead of 'cs' and 'cid'.

Any keyword arguments will be added as instance attributes.
```

### download
Download author info and post data and comments.
```python
def download(self):
# Example
p.download()
```

### set_word_weight_func
Sets a function that computes a word's weight based on the post and comment.
Called by `generate_word_counts()` to compute word weights. The function can
be accessed from `Post.word_weight` attribute.
```python
def set_word_weight_func(self, func):
# Example
def f(post_points, comment_votes, comment_level):
    return (post_points + comment_votes)/comment_level
p.set_word_weight_func(f)
```
```
Parameters:
- func (func):
    A function that accepts three arguments: post points, comment votes, and
    comment level. The function returns a float representing the word's
    weight.
```

### generate_word_counts
Split comments into words and tally their weights. Populates `Post.wordcount`.
```python
def generate_word_counts(self, child_comments=False, comment_votes=True,
                        comment_level=True):
# Example
p.generate_word_counts(comment_votes=False)
```
```
Parameters:
- comment_votes (bool):
    Whether to pass comment votes to Post.word_weight function or pass 1.

- child_comments (bool):
    Whether to parse child comments to make word counts.

- comment_level (bool):
    Whether to pass comment nest level to Post.word_weight function or pass 1.
    Top level comments have level=1.
```

### filter_by_weight
Filters (in or out) words in `Post.wordcount` by weights.
```python
def filter_by_weight(self, minimum, maximum, reverse=False):
# Examples
p.filter_by_weight(5,10)    # keep words with weights in [5,10] inclusive
p.filter_by_weight(5,10, reverse=True)    # keep words with weights not in
                                          # [5,10] inclusive
```
```
Parameters:
- minimum (float/int):
    Minimum inclusive threshold.

- maximum (float/int):
    Maximum inclusive threshold.

- reverse (bool):
    True: keep words below minimum and above maximum thresholds.
    False: keep words equal and above minimum, and equal and below maximum.
```

### filter_by_word
Filter `Post.wordcount` by words.
```python
def filter_by_word(self, words, reverse=False):
# Examples
p.filter_by_word(['my', 'name'])    # only keep word/weights for 'my' and 'name'
p.filter_by_word(['my', 'name'], reverse=True)    # discard word/weights for  
                                                  # 'my' and 'name'
```
```
Parameters:
- words (list/ndarray):
    A list of words to filter by.

- reverse (bool):
    True: discard word/weights for 'words'.
    False: discard all but word/weights for 'words'.
```

### sort_by_word
Sort `Post.wordcount` in ascending alphabetical order by 'word'.
```python
def sort_by_word(self):
# Examples
p.sort_by_word()
```

### sort_by_weight
Sort `Post.wordcount` in ascending numerical order by 'weight'.
```python
def sort_by_weight(self):
# Examples
p.sort_by_weight()
```

### sort
Sort `Post.wordcount` in default sort order (`config.DEFAULT_SORT_ORDER`)
```python
def sort(self):
# Examples
p.sort_by_weight()
```
