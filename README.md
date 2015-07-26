# imgurPCA
Machine Learning using clustering on imgur

Dependencies: [imgurpython](https://github.com/Imgur/imgurpython)

1. Parses comments by post on galleries, 
2. Filters out common words to create word vectors describing each post. 
3. *The vectors are then subjected to Principle Component Analysis to reduce data size and to make clustering easier.*
4. *New posts are parsed and transformed into the learned vector space and classified*
  
*The list of common words is taken from [here](http://www.wordfrequency.info/free.asp)*  
  
## Getting Started  
The imgurAPI class needs authorization to be able to access data on imgur. For that, you need [to get keys from imgur.com](https://api.imgur.com). You will be provided with a *client secret* and a *client id*. Use these to instantiate the imgurAPI class:  
```
import imgurAPI
imgurInstance = imgurAPI.imgurAPI(id, secret)
```  
After instantiation, you need to **get** items from imgur to parse. You can use the `get()` function for that. It accepts single strings, list of IDs, or a dictionary of [gallery specifications to extract content from](https://github.com/Imgur/imgurpython/blob/master/README.md). The list of IDs is stored in the `idlist` instance attribute.  
  
Now that the class instance has IDs of items to **parse**, you can begin parsing by calling the `parse()` function. You can specify the `cumulative` argument to either parse all items togther, or separately by their IDs. Another argument is `parsechildren` to specify if replies to comments are parsed or not. The result of parsing is stored in the `worddict` instance attribute. `worddict` is a dictionary in case of cumulative parsing, otherwise it is a dictionary of dictionaries.  
  
After that, you can **filter** the parsed data to remove any words of your choosing. The `filter()` function takes a *.csv* file path as an argument, and the number of words to read from it.  
  
In many cases the number of words parsed will be very large. It can be **truncated** by calling the `truncate()` function and specifying what number of the mose frequent words to keep. The list of most frequent words is made by tallying the entire dataset, not just a single item.
  
Some items will have words that others will not. For the sake of uniformity, missing words can be **consolidated**. The `consolodate()` function adds all words present in the cumulative tally but not in individual items to their dictionaries (with 0 counts).  
  
The words can be **sorted** by count in descending order by calling the `sort()` function.
  
The data can be **stored** to a csv file by calling the `store()` function that accepts an output file path as an argument. If the parsing was cumulative, then two rows (words; counts) are stored. Otherwise an array of values (word columns, per item ID count rows) is stored.  
  
The API allows for a limited number of requests and assigns **credits** to each key. Available credits can be viewwd by calling the `credits()` function.
  
Because of the way this code was written, successive functions can be chained for ease of use. For example:  
```
imgurInstance.get().parse(parsechildren=False, cumulative=False)
              .filter(num=1000).truncate(1000).sort().store().credits()
```  
Will **get** the default set of IDs, **parse** top level comments separately, **filter** out the top 100 words found in the default filter file, **truncate** all but the 1000 most frequent words from the dataset, **sort** them in order of cumulative frequency, then **store** them in the default output filepath, and at last show available **credits**.
