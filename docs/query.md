# imgurpca.Query
A helper class that constructs a valid query to be used by `Parser.get()`
function. Also includes checks to ensure query parameters are valid.  

### Attributes
```
- mode (int):
    Whatever Query was instantiated with. Used to find the appropriate API
    endpoint.

- content (dict):
    A dictionary containing the query parameters to be passed to the endpoint.
```

### Instantiation
```python
def __init__(self, what):
# Example
from imgurpca import Query
q = Query(Query.SUBREDDIT)
```
```
Parameters:
- what (int):
    Specifies which gallery/section on imgur to search. One of:
        * Query.GALLERY_TOP,
        * Query.GALLERY_HOT,
        * Query.GALLERY_USER,
        * Query.SUBREDDIT,
        * Query.MEMES,
        * Query.TAG,
        * Query.CUSTOM,
        * Query.RANDOM
```

### over
Specify the period over which to query.
```python
def over(self, ovr):
# Example
q.over(Query.WEEK)
```
```
Parameters:
- ovr (str):
    What period to query over. One of:
        * Query.DAY,
        * Query.WEEK,
        * Query.MONTH,
        * Query.YEAR,
        * Query.ALL
```

### sort_by
Specify the sorting order of results.
```python
def sort_by(self, sort):
Example:
q.sort_by(Query.TOP)
```
```
Parameters:
- sort (str):
    What metric to sort by. One of:
        * Query.TOP,
        * Query.TIME,
        * Query.RISING,
        * Query.VIRAL
```

### params
If a query mode needs parameters (like search terms for `Query.CUSTOM`),
specify them here.
```python
def params(self, q):
# Examples
q.params('pics')
```
```
Parameters:
- q (str):
    Search terms, subreddit names, tags for the appropriate query type.
```

### construct
Compile the query options into a dict that can be passed to an API endpoint.
After this, the query instance can be passed as an argument to `Parser.get()`.
```python
def construct(self):
# Example
q.construct()
```

NOTE: The entire process of query construction can be chained. For the above
examples:  
```python
q = Query(Query.SUBREDDIT).over(Query.WEEK).sort_by(Query.TOP)
    .params('pics').construct()
```
