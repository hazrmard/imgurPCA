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
        self.tally = collections.OrderedDict()

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

    def filter(self, fname='filter.csv', num=None):
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
            print "Filter complete."
        else:
            i = 0
            for itemkey in self.worddict:
                self.worddict[itemkey] = collections.OrderedDict({key: self.worddict[itemkey][key] for key in self.worddict[itemkey] if key not in filterlist})
                i += 1
                print "\rFilter " + "{0:.3g}% complete.".format(i*100/len(self.idlist)),
            self.tally = collections.OrderedDict({key: self.tally[key] for key in self.tally if key not in filterlist})
            print
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

    def consolidate(self):
        """make dictionary keys uniform"""
        if not self.cumulative:     # cumulative data needs no consolidation
            self.tally = collections.OrderedDict(sorted(self.tally.items(), key=lambda t: t[1], reverse=True))  # find most freq words in entire dataset
            i = 0       # counter
            datalength = len(self.idlist)
            tallykeys = set(self.tally.keys())                  # set of all words in all items
            for itemid in self.idlist:
                itemkeys = set(self.worddict[itemid].keys())    # set of words in a single item
                for key in tallykeys - itemkeys:                # iterating over set of words not in item but in tally
                    self.worddict[itemid][key] = 0              # adding them to item for uniformity
                i += 1
                print "\rConsolidating " + "{0:.3g}% complete.".format(i*100/datalength),
        print
        return self

    def sort(self):
        """sort words by frequency"""
        self.tally = collections.OrderedDict(sorted(self.tally.items(), key=lambda t: t[1], reverse=True))
        if self.cumulative:
            self.worddict = collections.OrderedDict(sorted(self.worddict.items(), key=lambda t: t[1], reverse=True))
        else:
            for itemid in self.worddict:
                self.worddict[itemid] = collections.OrderedDict(sorted(self.worddict[itemid].items(), key=lambda t: t[1], reverse=True))
        print "Sorting complete."
        return self

    def store(self, filename='word_dictionary.csv'):
        """store data to csv file"""
        f = open(filename, 'wb')                                    # write to csv
        fr = csv.writer(f)
        if self.cumulative:
            fr.writerow(self.worddict.keys())
            fr.writerow([self.worddict[key] for key in self.worddict])
        else:
            fr.writerow(['Item ID'] + self.tally.keys())
            for itemid in self.worddict:
                fr.writerow([itemid] + [self.worddict[itemid][key] for key in self.tally])
        f.close()
        print "Stored in " + filename + "."
        return self

    def truncate(self, num=None):
        self.consolidate()
        if num is not None:
            keys = self.tally.keys()[:num]      # truncate key list
            self.tally = collections.OrderedDict({key:self.tally[key] for key in keys})     # update tally
        if self.cumulative:
            self.worddict = collections.OrderedDict({key: self.worddict[key] for key in self.tally})
        else:
            for itemid in self.worddict:
                self.worddict[itemid] = collections.OrderedDict({key: self.worddict[itemid][key] for key in self.tally})
        print "Truncated to top " + str(num) + " words."
        return self

    def credits(self):
        """check usage with imgur API"""
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
                    if w in self.tally:     # to keep a cumulative tally of words for truncation and storing purposes
                        self.tally[w] += 1
                    else:
                        self.tally[w] = 1
                except:
                    continue
        else:
            for subcomment in comment.children:
                self.comment_extract(storage, subcomment, parsechildren)
