__author__ = 'Ibrahim'

# NOTE: currently under development. Part of a larger machine learning project I am working on.
# Functions extract comments from posts on imgur.com. The comments are converted to word vectors for
# processing. The data extracted from these functions will be subject to Principal Component Analysis and 
# unsupervised clustering.

from imgurpython import ImgurClient
import csv
import collections
import time


class imgurAPI:

    def __init__(self, cid, cs):
        self.clientID = cid
        self.clientSecret = cs
        self.client = ImgurClient(self.clientID, self.clientSecret)
        self.idlist = []
        self.worddict = collections.OrderedDict()
        self.isbatch = True
        self.cumulative = True

    # use function gallery_item_comments to get comments by item id

    def get(self, args=None):
        """obtain IDs of items to process"""
        if args is None:
            args = {'section': 'hot', 'sort': 'top', 'window': 'week', 'pages': 1}
        f = open('gallery_ids.txt', 'w')
        if type(args) == dict:
            for page in range(0, args['pages']):
                gallery = self.client.gallery(args['section'], args['sort'], page, args['window'])
                for item in gallery:
                    self.idlist.append(item.id.encode('utf-8'))
                    print >>f, item.id.encode('utf-8')
        elif type(args) == list:            # handle list of gallery IDs
            self.idlist = args
        elif type(args) == basestring:      # handle single ID
            self.isbatch = False
            self.idlist = [args]
        f.close()                           # file has new line at the end
        print str(len(self.idlist)) + " items loaded."
        return self

    def filter(self, fname='filter.csv', num=None):           # TODO: import filter list from csv + add option to specify count
        """read list of words to filter out from analysis"""
        f = open(str(fname), 'rb')
        r = csv.reader(f)
        filterlist = []
        if num is None:         # read entire file
            for row in r:
                filterlist.append(row)
        else:                   # read only some lines
            for i in range(num):
                filterlist.append(next(r))
        filterlist = [x[0].rstrip() for x in filterlist]
        f.close()
        if self.cumulative:
            self.worddict = collections.OrderedDict({key: self.worddict[key] for key in self.worddict if key not in filterlist})
        else:
            for itemkey in self.worddict:
                self.worddict[itemkey] = collections.OrderedDict({key: self.worddict[itemkey][key] for key in self.worddict[itemkey] if key not in filterlist})
        print "Filter complete."
        return self

    def parse(self, parsechildren=True, cumulative=True):
        """iterate over all comments and pass them on for processing"""
        i = 0.0             # counter
        self.cumulative = cumulative
        storage = self.worddict                                     # contains frequency of words as word:freq pair
        for itemid in self.idlist:
            try:
                if not self.cumulative:
                    self.worddict[itemid] = collections.OrderedDict()
                    storage = self.worddict[itemid]                 # create word dict for each item
                gallerycoments = self.client.gallery_item_comments(itemid)  # extract comments
                for comment in gallerycoments:
                    self.comment_extract(storage, comment, parsechildren)   # populate dictionary
                i += 1
                print "\rParsing " + "{0:.3g}% complete.".format(i*100/len(self.idlist)),
            except:
                print 'Error with item # ' + itemid                 # Getting a JSON response error with some items
        print
        return self

    def sort(self):
        if self.cumulative:
            self.worddict = collections.OrderedDict(sorted(self.worddict.items()), key=lambda t: t[1])
        else:
            for itemid in self.worddict:
                self.worddict[itemid] = collections.OrderedDict(sorted(self.worddict[itemid].items()), key=lambda t: t[1])

    def store(self, filename='word_dictionary.csv'):                # TODO: implement for cumulative=False
        tempdict = {}                                               # arrange in order of frequency
        if self.cumulative:
            for key in self.worddict:                                        # reverse word:freq as freq:[word]
                if self.worddict[key] in tempdict:
                    tempdict[self.worddict[key]].append(key)
                else:
                    tempdict[self.worddict[key]] = [key]
            templist = [key for key in tempdict]                        # extract list of all freqs
            templist.sort(reverse=True)                                 # arrange in descending order
            f = open(filename, 'wb')                                    # write to csv
            fr = csv.writer(f)
            for element in templist:                                    # write words in descending order to csv
                for item in tempdict[element]:
                    fr.writerow([item, element])
            f.close()
            print "Stored in " + filename + "."
        return self

    def credits(self):
        print "\nCredits:"
        print str(self.client.credits['UserRemaining']) + " remaining (IP based) out of " + str(self.client.credits['UserLimit'])
        print str(self.client.credits['ClientRemaining']) + " remaining (API key based) out of " + str(self.client.credits['ClientLimit'])
        print 'Credits Reset on: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.client.credits['UserReset']))
        return self

    def comment_extract(self, storage, comment, parsechildren):
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
                    if w in storage:
                        storage[w] += 1
                    else:
                        storage[w] = 1
                except:
                    continue
        else:
            for subcomment in comment.children:
                self.comment_extract(storage, subcomment, parsechildren)
