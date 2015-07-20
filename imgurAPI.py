__author__ = 'Ibrahim'

# NOTE: currently under development. Part of a larger machine learning project I am working on.
# Functions extract comments from posts on imgur.com. The comments are converted to word vectors for
# processing. The data extracted from these functions will be subject to Principal Component Analysis and 
# unsupervised clustering.

from imgurpython import ImgurClient
import csv
import collections


class imgurAPI:

    def __init__(self, cid, cs):
        self.clientID = cid
        self.clientSecret = cs
        self.client = ImgurClient(self.clientID, self.clientSecret)
        self.idlist = []
        self.worddict = {}

    # use function gallery_item_comments to get comments by item id

    def gallery_retrieval(self, section='hot', sort='top', window='week', pages=1):
        """retrieve ids of gallery items and output them to a file"""
        f = open('gallery_ids.txt', 'w')
        for page in range(0, pages):
            gallery = self.client.gallery(section, sort, page, window)
            for item in gallery:
                self.idlist.append(item.id.encode('utf-8'))
                print >>f, item.id.encode('utf-8')
        f.close()                           # file has new line at the end
        return self

    def filter_dict(self, worddict={}, fname='filter.txt'):
        """read list of words to filter out from analysis"""
        f = open(str(fname), 'r')
        filterlist = f.readlines()
        filterlist = [x.rstrip() for x in filterlist]
        f.close()
        tempdict = {key: worddict[key] for key in worddict if key not in filterlist}
        return tempdict

    def comment_parse(self, parsechildren=True, cumulative=True):
        """iterate over all comments and pass them on for processing"""
        worddict = {}                                               # contains frequency of words as word:freq pair
        for itemid in self.idlist:
            print itemid                                            # perhaps add functionality for a log file
            try:
                gallerycoments = self.client.gallery_item_comments(itemid)
                for comment in gallerycoments:
                    self.comment_extract(worddict, comment, parsechildren)
            except:
                print 'Error with item # ' + itemid                 # Getting a JSON response error with some items
        worddict = self.filter_dict(worddict)                       # apply filter
        tempdict = {}                                               # arrange in order of frequency
        for key in worddict:                                        # reverse word:freq as freq:[word]
            if worddict[key] in tempdict:
                tempdict[worddict[key]].append(key)
            else:
                tempdict[worddict[key]] = [key]
        templist = [key for key in tempdict]                        # extract list of all freqs
        templist.sort(reverse=True)                                 # arrange in descending order
        f = open('word_dictionary.csv', 'wb')                       # write to csv
        fr = csv.writer(f)
        for element in templist:                                    # write words in descending order to csv
            for item in tempdict[element]:
                fr.writerow([item, element])
        f.close()
        return self

    def comment_extract(self, worddict, comment, parsechildren):
        """recursively parse comments and split them to form a dictionary"""
        dellist = [x for x in '''!@#$%^&*()-`~_=+{[}]:;,<.>/?\|'")0123456789''']
        if not comment.children or not parsechildren:
            cmt = comment.comment.lower()
            for c in dellist:               # replacing unwanted characters from comment
                cmt = cmt.replace(c, '')
            cmt = cmt.split()               # splitting comment into words
            for word in cmt:
                try:                        # only processing ascii character words
                    w = str(word)
                    if w in worddict:
                        worddict[w] += 1
                    else:
                        worddict[w] = 1
                except:
                    continue
        else:
            for subcomment in comment.children:
                self.comment_extract(worddict, subcomment, parsechildren)
