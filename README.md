# imgurPCA v2
Machine Learning using clustering on imgur. Under development. Basic interface 
is complete.  

`imgurpca` is a package that uses Principal Component Analysis to extract
patterns from comments on *imgur.com*. It also provides a way to automate tasks
like posting to/ getting notifications from imgur.  
  
[Principal Component Analysis (PCA)](https://en.wikipedia.org/wiki/Principal_component_analysis)
is a way to reduce the dimensionality of data points. For a given set of data, 
it finds vectors that best describe a sample's distribution. Those vectors 
can be used as axes for later computations. For example, posts on *imgur.com* may 
have thousands of unique words which would mean thousands of dimensions in the 
data. But with PCA, a few vectors can be used to distinquish posts without 
significant loss in accuracy.  
  
With fewer vectors needed to describe posts and users (by their comments) 
other computations become less costly. For example, you can try to predict:  

* What score a comment would get based on existing gallery comments (linear regression),
* If a user is likely to favourite a post based on their history (logistic regression),
* Posts that are similar in 'tone' (k-means clustering).
  
`imgurpca` also provides the `Bot` class. It can post comments, upload pictures, 
send messages etc. interactively or in the backround on whatever schedule you choose.  
  
See [`docs`](./docs/) folder for more details on usage.  
  
### About
This was my first ever project on github. I had left it in suspension in 
favour of other things to do. I came back more than a year later (*as was prophesized*) 
to finish this. If you compare [last year's version `v1`](https://github.com/hazrmard/imgurPCA/tree/911167f611e017ee143fc56a369ad383fff2c3e8) 
with this one (`v2`) you'll notice quite a change in approach. That's the lesson here folks, 
~~procrastinate for a year~~ `# TODO: finish the joke`.


