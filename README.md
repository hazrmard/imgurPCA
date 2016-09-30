# imgurPCA v2
Machine Learning on imgur. Under development. Basic interface is complete.  

`imgurpca` is a set of tools that help parse, analyze, and act on textual data on
*imgur.com*. It provides a modular interface that lets you build trivial to
complex workflows. From making a random comment bot, to systemically detecting
and downvoting memes and posts about cats: you can do it all. The latter was my
primary motivation for this project, but that's another story.

While initially written for *imgur*, the project has been structured so that it
can be easily ported to another API. Additionally, many machine learning
functions in `imgurpca` can be universally used with any data set out of the box.

`imgurpca` provides an option to use [Principal Component Analysis (PCA)](https://en.wikipedia.org/wiki/Principal_component_analysis)
as a way to reduce the dimensionality of data points. For a given set of data,
it finds vectors that best describe the set's distribution. Those vectors
can be used as axes for later computations. For example, posts on *imgur.com* may
have thousands of unique words which would mean thousands of dimensions in the
data. But with PCA, a few vectors can be used to distinguish posts without
significant loss in accuracy.  

With fewer vectors needed to describe posts and users (by their comments),
other computations become less costly. For example, you can try to predict:  

* What score a comment would get based on existing gallery comments (**linear regression**),
* If a user is likely to favourite a post based on their history (**logistic regression**),
* Posts that are similar in 'tone' (**k-means clustering**),
* Tags a post would get based on comments/title/description (**decision tree**).

All of the machine learning methods above in parentheses have been implemented
in the `Learner` class, with more to come.

`imgurpca` also provides the `Bot` class. It can post comments, upload pictures,
send messages etc. interactively or in the backround on whatever schedule you choose.  

See [`docs`](./docs/) folder for more details on usage.  

### About
This was my first ever project on github. I had left it in suspension in
favour of other things to do. I came back more than a year later to finish this.
If you compare [last year's version `v1`](https://github.com/hazrmard/imgurPCA/tree/911167f611e017ee143fc56a369ad383fff2c3e8)
with this one (`v2`) you'll notice quite a change in approach. That's the lesson here folks,
~~procrastinate for a year~~ `# TODO: finish the joke`.
