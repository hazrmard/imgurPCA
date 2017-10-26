# imgurPCA v2

`imgurpca` is a modular text analysis and machine learning library. It uses post
comments on [imgur][1] as its corpus.

![Logo](./imgurpca_logo.png)

`imgurpca` contains a set of tools that help parse, analyze, and act on insights
gained from textual data. A modular design allows for complex workflows.

While initially written for [imgur][1], the project has been structured so that it
can be easily ported to another data source/API. Core class definitions are
present in `imgurpca\base` which can be subclassed for different needs.

`imgurpca` bases all processing on [Principal Component Analysis (PCA)][2]
as a way to reduce the dimensionality of data points. A data point can be the
set of comments made by a user, or comments on a single post. There can be
thousands of unique words describing a set of points. Analysing such data becomes
intractable (see [Curse of dimensionality][3]). For a given set of data,
it finds vectors of words that best describe the set's distribution. Those vectors
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
send messages etc. interactively or in the backround on a schedule.

See [`docs`](./docs/) folder for more details on usage.

## About

This was my first ever personal open-source project. I had left it in suspension in
favour of other things to do. I came back more than a year later to add features
and fix bugs here and there. If you compare [last year's version `v1`][4] with
this one (`v2`) you'll notice quite a change in approach. That's the lesson here folks, ~~procrastinate for a year~~ `# TODO: finish the joke`.

**Disclaimer**: Performance of my implementation may not be optimal. This project
was an exercise in using my machine learning knowledge. Where possible I coded
features from scratch.


[1]: https://imgur.com
[2]: https://en.wikipedia.org/wiki/Principal_component_analysis
[3]: https://en.wikipedia.org/wiki/Curse_of_dimensionality
[4]: https://github.com/hazrmard/imgurPCA/tree/911167f611e017ee143fc56a369ad383fff2c3e8