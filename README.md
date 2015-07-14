# imgurPCA
Machine Learning using clustering on imgur

Dependencies: [imgurpython](https://github.com/Imgur/imgurpython)

1. Parses comments by post on galleries, 
2. Filters out common words to create word vectors describing each post. 
3. *The vectors are then subjected to Principle Component Analysis to reduce data size and to make clustering easier.*
4. *New posts are parsed and transformed into the learned vector space and classified*
