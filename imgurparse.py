__author__ = 'Ibrahim'

# NOTE: currently under development. Part of a larger machine learning project I am working on.
# Functions extract comments from posts on imgur.com. The comments are converted to word vectors for
# processing. The data extracted from these functions will be subject to Principal Component Analysis and 
# unsupervised clustering.

from imgurpython import ImgurClient
import csv
import collections
import time


class ImgurParse:

    def __init__(self, cid=None, cs=None):
        self.clientID = cid
        self.clientSecret = cs
        if cid and cs:
            self.client = ImgurClient(self.clientID, self.clientSecret)
        self.idlist = []
        self.worddict = collections.OrderedDict()
        self.exceptflag = False
        self.cumulative = False
        self.tally = collections.OrderedDict()
        self.exceptions = set()

    # use function gallery_item_comments to get comments by item id

    def get(self, args=None):
        """obtain IDs of items to process"""
        if args is None:
            args = {'section': 'hot', 'sort': 'top', 'window': 'week', 'pages': 1}
        if type(args) == dict:
            for page in range(0, args['pages']):
                gallery = self.client.gallery(args['section'], args['sort'], page, args['window'])
                for item in gallery:
                    self.idlist.append(item.id.encode('utf-8'))
        elif type(args) == list:            # handle list of gallery IDs
            self.idlist = args
        elif type(args) == basestring:      # handle single ID
            self.idlist = [args]
        print str(len(self.idlist)) + " items loaded."
        self.idlist = [itemid for itemid in set(self.idlist) - self.exceptions]             # filter out exceptions
        self.exceptions = set()
        return self

    def exceptfor(self, what):
        """specifies items that need to be excluded from get and load functions"""
        self.exceptflag = True
        if type(what) == list:
            self.exceptions = set(what)
        elif type(what) == basestring:
            self.exceptions = set(what)
        elif isinstance(what, ImgurParse):
            self.exceptions = set(what.idlist)
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
            i = 0.0
            for itemkey in self.worddict:
                self.worddict[itemkey] = collections.OrderedDict({key: self.worddict[itemkey][key] for key in self.worddict[itemkey] if key not in filterlist})
                i += 1
                print "\rFilter " + "{0:.3g}% complete.".format(i*100/len(self.idlist)),
            self.tally = collections.OrderedDict({key: self.tally[key] for key in self.tally if key not in filterlist})
            print
        return self

    def parse(self, parsechildren=True, cumulative=None):
        """iterate over all comments and pass them on for processing"""
        i = 0.0             # counter
        if cumulative is None:
            cumulative = self.cumulative
        else:
            self.cumulative = cumulative
        storage = self.worddict                                     # contains frequency of words as word:freq pair
        for itemid in self.idlist:
            try:
                if not cumulative:
                    self.worddict[itemid] = collections.OrderedDict()
                    storage = self.worddict[itemid]                 # create word dict for each item
                gallerycoments = self.client.gallery_item_comments(itemid)  # extract comments
                for comment in gallerycoments:
                    self._comment_extract(storage, comment, parsechildren)   # populate dictionary
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
            i = 0.0       # counter
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
            print "Sorting 100% complete."
        else:
            i = 0.0
            for itemid in self.worddict:
                self.worddict[itemid] = collections.OrderedDict(sorted(self.worddict[itemid].items(), key=lambda t: t[1], reverse=True))
                i += 1
                print "\rSorting " + "{0:.3g}% complete.".format(i*100/len(self.idlist)),
            print
        return self

    def store(self, filename='word_dictionary.csv'):
        """store data to csv file"""
        f = open(filename, 'wb')                                    # write to csv
        fr = csv.writer(f)
        if self.cumulative:
            fr.writerow(self.worddict.keys())                               # write keys,
            fr.writerow([self.worddict[key] for key in self.worddict])      # and values,
            fr.writerow(self.idlist)                                        # and IDs
        else:
            fr.writerow(['Item ID'] + self.tally.keys())
            for itemid in self.worddict:
                fr.writerow([itemid] + [self.worddict[itemid][key] for key in self.tally])
        f.close()
        print "Stored in " + filename + "."
        return self

    def load(self, source, cumulative=None):
        """loads from csv if source is string, or from dict otherwise"""
        if cumulative is None and self.worddict:    # cumulative not specified, instance contains data
            cumulative = self.cumulative
        elif cumulative is not None and not self.worddict:  # cumulative specified, instance does not contain data
            self.cumulative = cumulative
        elif cumulative != self.cumulative and self.worddict:   # cumulative spec not same, and data already exists
            raise ValueError("Cumulative and non-cumulative sources cannot be matched.")
        if type(source) == str:
            if cumulative:
                self._read_cumulative(source)
            else:
                self._read_noncumulative(source)
                print 'non cumulative'
        elif isinstance(source, ImgurParse):
            if (not self.cumulative and set(self.idlist).isdisjoint(set(source.idlist) - self.exceptions)) or (self.cumulative and set(self.idlist).isdisjoint(set(source.idlist))):       # only combine if IDs are mutually exclusive
                self.idlist.append(source.idlist)
                if cumulative:                                          # add wordcounts
                    mykeys = set(self.worddict.keys())
                    sourcekeys = set(source.worddict.keys())
                    ourkeys = mykeys & sourcekeys
                    onlysourcekeys = sourcekeys - mykeys
                    for key in ourkeys:
                        self.worddict[key] += source.worddict[key]
                    for key in onlysourcekeys:
                        self.worddict[key] = source.worddict[key]
                else:                                                   # append source data to self.worddict
                    for itemid in set(source.idlist) - self.exceptions:
                        self.worddict[itemid] = source.worddict[itemid]
                    self.exceptions = set()
                    self.exceptflag = False
            else:
                raise ValueError('The lists of IDs are not disjoint.')

        self.idlist = [itemid for itemid in set(self.idlist) - self.exceptions]             # filter out exceptions
        self.exceptions = set()
        self.exceptflag = False
        print "Loading complete."
        return self

    def omit(self, arg):                                    # TODO: omit by specifying frequency ranges
        """remove keys by specifying frequency range"""
        pass

    def truncate(self, num, cumulative=None):
        """shorten list of words by frequency rank"""
        if cumulative is None:
            cumulative = self.cumulative
        if cumulative and self.cumulative:
            if num > 0:
                keys = self.tally.keys()[:num]      # truncate key list (bottom or top)
            else:
                keys = self.tally.keys()[len(self.tally.keys() + num):]
            self.worddict = collections.OrderedDict({key: self.worddict[key] for key in self.tally})
            self.tally = collections.OrderedDict({key: self.tally[key] for key in keys})     # update tally
            print "Truncation complete."
        elif cumulative and not self.cumulative:    # truncate individual records on cumulative basis
            i = 0.0
            if num > 0:
                keys = self.tally.keys()[:num]      # truncate key list (bottom or top)
            else:
                keys = self.tally.keys()[len(self.tally.keys() + num):]
            self.tally = collections.OrderedDict({key: self.tally[key] for key in keys})     # update tally
            for itemid in self.worddict:
                keyset = set(self.worddict[itemid].keys())
                keyset = keyset - set(keys)     # get set of keys in the keyset but not in the tally
                for key in keyset:
                    del self.worddict[itemid][key]
                i += 1
                print "\rTruncating " + "{0:.3g}% complete.".format(i*100/len(self.idlist)),
            print
        elif not cumulative and not self.cumulative:    # truncate individual records on individual basis
            keyset = set()          # store words still existing in dicts
            i = 0.0
            for itemid in self.worddict:
                if num > 0:
                    keys = self.worddict[itemid].keys()[:num]      # truncate key list
                else:
                    keys = self.worddict[itemid].keys()[len(self.worddict[itemid].keys()) + num:]
                keyset.update(keys)
                self.worddict[itemid] = collections.OrderedDict({key: self.worddict[itemid][key] for key in keys})
                i += 1
                print "\rTruncating " + "{0:.3g}% complete.".format(i*100/len(self.idlist)),
            print
            removekeys = set(self.tally.keys()) - keyset        # keys that no longer exist
            for key in removekeys:
                del self.tally[key]
        else:
            raise ValueError('Cannot truncate individually on cumulatively parsed data.')
        return self

    def credits(self):
        """check usage with imgur API"""
        print "\nCredits:"
        print str(self.client.credits['UserRemaining']) + " remaining (IP based) out of " + str(self.client.credits['UserLimit'])
        print str(self.client.credits['ClientRemaining']) + " remaining (API key based) out of " + str(self.client.credits['ClientLimit'])
        print 'Credits Reset on: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.client.credits['UserReset']))
        return self

    def normalize(self):
        if self.cumulative:
            totalcount = float(sum(self.worddict.values()))
            for key in self.worddict.keys():
                self.worddict[key] /= totalcount
        else:
            for itemid in self.worddict.keys():
                totalcount = float(sum(self.worddict[itemid].values()))
                for word in self.worddict[itemid].keys():
                    self.worddict[itemid][word] /= totalcount
        print "Normalized"
        return self

    def _comment_extract(self, storage, comment, parsechildren):
        """recursively parse comments and split them to form a dictionary"""
        dellist = [x for x in '''!@#$%^&*()-`~_=+{[}]:;,<.>/?\|'")0123456789''']
        if not comment.children or not parsechildren:
            cmt = comment.comment.lower()
            for c in dellist:               # replacing unwanted characters from comment
                cmt = cmt.replace(c, '')
            cmt = cmt.split()               # splitting comment into words
            self._tally(storage, cmt)
        else:
            for subcomment in comment.children:
                self._comment_extract(storage, subcomment, parsechildren)

    def _read_cumulative(self, source):
        """add cumulatively stored keys/counts to class instance from csv file"""
        f = open(source)
        r = csv.reader(source)
        sourcekeys = r.next()
        sourcevals = r.next()
        sourcevals = [int(x) for x in sourcevals]
        sourcedict = {sourcekeys[i]: sourcevals[i] for i in range(len(sourcekeys))}
        sourceids = set(r.next()) - self.exceptions
        if set(self.idlist).isdisjoint(sourceids):
            existingkeys = set(self.worddict.keys()) - set(sourcekeys)
            newkeys = set(sourcekeys) - set(self.worddict.keys())
            for key in existingkeys:
                self.worddict[key] += sourcedict[key]
            for key in newkeys:
                self.worddict[key] = 0
        else:
            raise ValueError('Target and Self IDs are not disjoint.')
        f.close()

    def _read_noncumulative(self, source):
        """add individually stored keys/counts to class instance from csv file"""
        f = open(source)
        r = csv.DictReader(f)
        for row in r:
            if row['ItemId'] in self.idlist:
                raise ValueError('Target and self IDs are not disjoint.')
            elif row['ItemId'] not in self.exceptions:
                itemid = row['ItemId']
                self.idlist.append(itemid)
                del row['ItemId']
                row = collections.OrderedDict(self._dict2int(row))
                self.worddict[itemid] = row
                self._tally(self.worddict, row)
        f.close()
        pass

    def _dict2int(self, d):
        """convert dictionary values into integers from strings"""
        for key in d:
            d[key] = int(d[key])
        return d

    def _tally(self, storage, wordlist):
        """take either a dictionary or a list of words and add them to tally"""
        try:
            for word in wordlist.keys():
                try:                        # only processing ascii character words
                    w = str(word)
                    if w in storage:
                        storage[w] += wordlist[word]
                    else:
                        storage[w] = wordlist[word]
                    if w in self.tally:     # to keep a cumulative tally of words for truncation and storing purposes
                        self.tally[w] += wordlist[word]
                    else:
                        self.tally[w] = wordlist[word]
                except:
                    continue
        except:
            for word in wordlist:
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
