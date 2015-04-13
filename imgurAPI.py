__author__ = 'Ibrahim'

# NOTE: currently under development. Part of a larger machine learning project I am working on.
# Functions extract comments from posts on imgur.com. The comments are converted to word vectors for
# processing. The data extracted from these functions will be subject to Principal Component Analysis and 
# unsupervised clustering.

from imgurpython import ImgurClient
import csv

client_id = '***REMOVED***'
client_secret = '***REMOVED***'

client = ImgurClient(client_id, client_secret)

# use function gallery_item_comments to get comments by item id


def gallery_retrieval(section='hot', sort='top', window='week', pages=1):
    """retrieve ids of gallery items and output them to a file"""
    idlist = []
    f = open('gallery_ids.txt', 'w')
    for page in range(0, pages):
        gallery = client.gallery(section, sort, page, window)
        for item in gallery:
            idlist.append(unicode(item.id))
            print >>f, unicode(item.id)
    f.close()                           # file has new line at the end
    return idlist


def filter_dict(worddict, fname='filter.txt'):
    """read list of words to filter out from analysis"""
    f = open(fname, 'r')
    filterlist = f.readlines()
    filterlist = [x.rstrip() for x in filterlist]
    f.close()
    tempdict = {key: worddict[key] for key in worddict if key not in filterlist}
    return tempdict


def comment_parse(idlist, parsechildren=True, filterdict=None):
    """iterate over all comments and pass them on for processing"""
    worddict = {}
    # parse comments
    # open csv file here to store gallery comment vectors
    for itemid in idlist:
        print itemid                                            # perhaps add functionality for a log file
        try:
            gallerycoments = client.gallery_item_comments(itemid)
        except:
            print 'Error with item # ' + itemid                 #Getting a JSON response error with some items
        for comment in gallerycoments:
            comment_extract(worddict, comment, parsechildren)
    #apply filter
    worddict = filter_dict(worddict)
    #arrange in order of frequency
    tempdict = {}
    for key in worddict:
        if worddict[key] in tempdict:
            tempdict[worddict[key]].append(key)
        else:
            tempdict[worddict[key]] = [key]
    templist = [key for key in tempdict]
    templist.sort(reverse=True)
    # write to csv
    f = open('word_dictionary.csv', 'wb')
    fr = csv.writer(f)
    worddict = {}
    for element in templist:
        for item in tempdict[element]:
            worddict[item] = element
            fr.writerow([item.encode('utf8'), element])
    f.close()
    return worddict





def comment_extract(worddict, comment, parsechildren):
    """recursively parse comments and split them to form a dictionary"""
    dellist = [x for x in '''!@#$%^&*()-`~_=+{[}]:;,<.>/?\|'")0123456789''']
    if not comment.children or not parsechildren:
        cmt = comment.comment.lower()
        for c in dellist:
            cmt = cmt.replace(c, '')
        cmt = cmt.split()
        for word in cmt:
            if word in worddict:
                worddict[word] += 1
            else:
                worddict[unicode(word)] = 1
    else:
        for subcomment in comment.children:
            comment_extract(worddict, subcomment, parsechildren)
