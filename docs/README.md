# imgurpca
Machine learning with imgur. *pca* stands for Principal Component Analysis.  

`imgurpca` is a set of tools that parse and analyse content on imgur.com. In
addition it can act on behalf of a user interactively or through scheduled
actions. This package needs approval from the API to be able to access data.
The user needs to register their application with the API and get a `client
secret` and `client id`.  

## Installation
Clone this repository:  
```bash
>> git clone https://github.com/hazrmard/imgurPCA.git
```
Navigate to repository root:  
```bash
>> cd imgurPCA
```
Run install:  
```bash
>> python setup.py install
```

## Getting Started
First go to [imgur settings](https://imgur.com/account/settings/apps) and
register your application. Once you have the `client id` and `client secret`
copy them into the placeholders at the beginning of `test.py`. Then run:  
```bash
>> python test.py
```
to begin testing. The tests will be verbose and will give an idea of that the
package can do. Once all tests are successful, you can begin using the package
classes.  
```python
from imgurpca import *
```
`imgurpca` provides several classes which neatly fit into a workflow for data
analysis:  
```
 ---------
|  Post   |----→----------→--------------⬎
 ---------     ↓      ---------       ----↓----       ---------
               |----→| Parser  |----→| Learner |----→|   Bot   |
 ---------     ↑      ----↑----       ----↑----       ---------
|  User   |----→----------|--------------⬏
 ---------            ----|----
                     |  Query  |
                      ---------
```  
* **Post** is a representation of a single gallery post on imgur. It downloads,
sanitizes, and filters content on a post.
* **User** is a representation of a single user's activity and exposes (more
    or less) the same interface as *Post*.
* **Parser** performs collective actions on *Post* or *User* objects. It can
also directly query imgur for posts.
* **Query** constructs a valid query that is used as a common argument to
access the imgur API's various endpoints.
* **Learner** uses *Parser*/*Post*/*User* objects to set up axes that best
describe the data. Using them it can perform regression and clustering
operations on *Post*/*User* objects.
* **Bot** can get authenticated and act on behalf of a user. It can also
periodically perform tasks (like uploading, commenting etc.).

The class APIs are explained in further detail in their respective `.md` files.
