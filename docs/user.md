# imgurpca.User
`User` represents a single user's comments on imgur. It is subclassed from
`Post`.

### Attributes
```
- url (str):
    The username of the user.

- username (str):
    An alias for url. Read only.

- reputation (int):
    The user's reputation. Populated after download().

- points (int):
    An alias for reputation. Read only. For compatibility with Post class.

- comments (list):
    A list of comment objects (see imgur API data models) associated with the
    user.

- content (list):
    An alias for comments. Read only.

- network (list):
    A list of post ids (str) associated with the user.  Alias for
    User.get_post_ids. Read only.

- favourites (list):
    Gallery items the user has favourited. Populated after download(). Items
    are Gallery Image/Album objects. See imgur API data models.

- posts (list):
    Posts made and shared by the user. Post objects have attributes of a
    Gallery Image or a Gallery Album. See imgur API data models for details.
    Populated after download().

- wordcount (ndarray):
    A numpy array of words and their weights. Of dtype=config.DT_WORD_WEIGHT.
    Each element has 2 fields: 'word' (10 char unicode) and 'weight' (float).
    Populated after generate_word_counts().

- words (ndarray):
    A numpy array of words in wordcount. Same as User.wordcount['word']. Of
    dtype=config.DT_WORD. Read only.

- weights (ndarray):
    A numpy array of weights in wordcount. Same as User.wordcount['weight']. Of
    dtype=config.DT_WEIGHT. Read only.

- word_weight (func):
    A function object that takes three arguments: post points, comment vote,
    and comment level. Used by generate_word_counts(). For User instances,
    post points and comment level default to 1. This is because User uses
    Post's generate_word_counts(). Defaults to config.DEFAULT_WORD_WEIGHT.

- cs (str):
    The client secret. Set at instantiation.

- cid (str):
    The client id. Set at instantiation.

- client (ImgurClient):
    An instance of imgurpython.ImgurClient. Exposes entire imgurpython API.

In addition, after download() is called attributes in the 'account' data model
are also assigned to the instance. See imgur API data models for details.
```

### Instantiation
```python
def __init__(self, url, *args, **kwargs):
# Example
from imgurpca import User
u = User('harrypotter', cs='my client secret', cid='my client id')
```
```
Parameters:
- url (str):
    The username of an account. It is called 'url' in the API data model.

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
Download user account info, posts, favourites, and comments. Imgur API
paginates responses. Successive calls append to previous results.
```python
def download(self, pages=0):
# Example
u.download(pages=(0,5))     # get pages 0,1,2,3,4
u.download(pages=5)         # get page 5
```
```
Parameters:
- pages (int/tuple):
    Page[s] to download. Tuple downloads range, int downloads single page.
```

### set_word_weight_func
Sets a function that computes a word's weight based on the post and comment.
Called by `generate_word_counts()` to compute word weights. The function can
be accessed from `User.word_weight` attribute.
```python
def set_word_weight_func(self, func):
# Example
def f(post_points, comment_votes, comment_level):
    return (post_points + comment_votes)/comment_level
u.set_word_weight_func(f)
```
```
Parameters:
- func (func):
    A function that accepts three arguments: post points, comment votes, and
    comment level. The function returns a float representing the word's
    weight. Post points and comment level are defaulted to 1 for User.
```

### generate_word_counts
Split comments into words and tally their weights. Populates `User.wordcount`.
```python
def generate_word_counts(self, comment_votes=True, *args, **kwargs):
# Example
u.generate_word_counts(comment_votes=False)
```
```
Parameters:
- comment_votes (bool):
    Whether to pass comment votes to User.word_weight function or pass 1.
```

### filter_by_weight
Filters (in or out) words in `User.wordcount` by weights.
```python
def filter_by_weight(self, minimum, maximum, reverse=False):
# Examples
u.filter_by_weight(5,10)    # keep words with weights in [5,10] inclusive
u.filter_by_weight(5,10, reverse=True)    # keep words with weights not in
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
Filter `User.wordcount` by words.
```python
def filter_by_word(self, words, reverse=False):
# Examples
u.filter_by_word(['my', 'name'])    # only keep word/weights for 'my' and 'name'
u.filter_by_word(['my', 'name'], reverse=True)    # discard word/weights for  
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
Sort `User.wordcount` in ascending alphabetical order by 'word'.
```python
def sort_by_word(self):
# Examples
u.sort_by_word()
```

### sort_by_weight
Sort `User.wordcount` in ascending numerical order by 'weight'.
```python
def sort_by_weight(self):
# Examples
u.sort_by_weight()
```

### sort
Sort `User.wordcount` in default sort order (`config.DEFAULT_SORT_ORDER`)
```python
def sort(self):
# Examples
u.sort_by_weight()
```
