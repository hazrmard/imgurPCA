from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from imgurpca import *
from imgurpca.base import Parallel
from imgurpca.macros import Chatter
from imgurpython import ImgurClient
from imgurpython.client import ImgurClientError
import pickle
import numpy as np
import os
import time
import sys
import requests

SAMPLE_POST = None
SAMPLE_USER = None
SAMPLE_PARSER = None
SAMPLE_LEARNER = None
SAMPLE_BOT = None

TESTS_PASSED = 0
TESTS_FAILED = 0

try:
    from myconfig import CS as CLIENT_SECRET
    from myconfig import CID as CLIENT_ID
except ImportError: # manually set secret and ID
    CLIENT_SECRET = ''
    CLIENT_ID = ''
CLIENT = ImgurClient(CLIENT_ID, CLIENT_SECRET)

try:
    basestring
except NameError:
    basestring = str    # python 3 compatibility

def get_test_data(c):
    pass

def test(fn):
    def wrapper(*args, **kwargs):
        print('{:<45}'.format(args[0]), end='')
        try:
            fn(*args[1:], **kwargs)
            print('{:>10}'.format('\tSUCCESS'))
            global TESTS_PASSED
            TESTS_PASSED += 1
        except Exception as e:
            print('{:>20}'.format('\tFAULURE - ' + str(e)))
            global TESTS_FAILED
            TESTS_FAILED += 1
        print()
    return wrapper

def print_credits():
    global CLIENT
    credits = imutils.get_credits(CLIENT)
    [print(x[0]+': '+str(x[1]),end='; ') for x in credits.items()]
    print()
    if credits['UserRemaining']==0:
        print('Usage limit exceeded. Retry after %s.' % credits['UserReset'])
        exit(-1)


@test
def test_post_instance(c):
    """check if instantiation of Post works with accentable arguments"""
    p = Post(123, comments=['123', 'abc'], client=c)
    try:
        p = Post(123, comments=['123', 'abc'], cs='123fasfa', cid='asdeerwwe33')
    except ImgurClientError:
        pass
    try:
        p = Post(123)
        raise Exception('InvalidArgument expected.')
    except config.InvalidArgument:
        pass

@test
def test_post_download(c):
    """check if all post/comment/user data can be downloaded"""
    global SAMPLE_POST
    SAMPLE_POST = Post('b91LE', client=c)
    SAMPLE_POST.download()
    try:
        p = Post('123', client=c)
        p.download()
        raise Exception('ImgurClientError expected.')
    except ImgurClientError:
        pass

@test
def test_post_user_extraction(c):
    if SAMPLE_POST is None:
        raise ValueError('Depends on download test success.')
    ids = SAMPLE_POST.get_user_ids()
    assert isinstance(ids, (list,tuple)) and len(ids)>0 and isinstance(ids[0], basestring),\
            'ids non-list/tuple OR ids 0-length OR ids non-string'

@test
def test_user_instance(c):
    u = User('blah', client=c)
    try:
        u = User(123)
        raise Exception('InvalidArgument exception expected.')
    except config.InvalidArgument:
        pass

@test
def test_user_download(c):
    global SAMPLE_USER
    SAMPLE_USER = User('apitester', client=c)
    SAMPLE_USER.download(pages=(0,100))
    try:
        u = User('123', client=c)
        u.download()
        raise Exception('ImgurClientError expected.')
    except ImgurClientError:
        pass

@test
def test_user_post_extraction(c):
    if SAMPLE_USER is None:
        raise ValueError('Depends on download test success.')
    ids = SAMPLE_USER.get_post_ids()
    assert isinstance(ids, (list,tuple)) and len(ids)>0 and isinstance(ids[0], basestring),\
            'ids non-list/tuple OR ids 0-length OR ids non-string'

@test
def test_structure_flattening(c):
    """check if arbitrarily nested comments can be flattened for parsing"""
    p = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + 'testdata' +\
                                                os.sep + 'test_comment.object'
    with open(p, 'rb') as f:
        comments = pickle.load(f)             # a serialized comment object w/ known values
    n=0
    for c in utils.flatten(comments, accessor=lambda x: x.children):
        n+=1
    if n!=54:
        raise ValueError('Comment object incorrectly flattened.')
    l = [[1,2,[3,[4,5]]],6,7,[8,9,[10]]]
    n=0
    for i in utils.flatten(l, accessor=lambda x: x):
        n+=1
        assert n==i[0], 'Incorrect result from flattened generator.'
    assert n==10, 'Nested list incorrectly flattened.'

@test
def test_sentence_sanitation(c):
    """check if sentences can be correctly decomposed into words"""
    s = 'THE QuiCK !brO-Wn.'
    expected = ['the', 'quick', 'brown']
    res = utils.sanitize(s)
    if res != expected:
        raise ValueError('Unexpected sentence decomposition.')

@test
def test_word_counts(c):
    """check if parsing funcs work w/ current imgur data structure"""
    obj = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + 'testdata'+os.path.sep+'test_comment.object'
    with open(obj, 'rb') as f:
        comments = pickle.load(f)             # a serialized comment object w/ known values
    p = Post('asd',client=c, comments=comments, points=100)
    p.generate_word_counts(child_comments=False, comment_votes=True,
                            comment_level=True)
    p.generate_word_counts(child_comments=False, comment_votes=True,
                            comment_level=False)
    p.generate_word_counts(child_comments=True, comment_votes=True,
                            comment_level=True)
    global SAMPLE_USER
    global SAMPLE_POST
    if SAMPLE_USER is None or SAMPLE_POST is None:
        raise ValueError('Depends on download test success.')
    SAMPLE_USER.generate_word_counts()      # User has no child_comments option
    SAMPLE_POST.generate_word_counts(child_comments=True)

@test
def test_normalization(c):
    arr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    brr = np.array([1,2,3,4,5]) / 15.0
    p = Post(id='xyz', client=c, wordcount=arr)
    p.normalize()
    assert np.array_equal(p.weights, brr), 'Incorrect normalization.'

@test
def test_weight_filters(c):
    arr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    brr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    arr1 = np.array([('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    arr2 = np.array([('a',1),('b',2)],dtype=config.DT_WORD_WEIGHT)
    p = Post('asd', wordcount=arr, client=c)
    p.filter_by_weight(3,5)
    q = Post('def',wordcount=brr, client=c)
    q.filter_by_weight(3,5,True)
    if not (np.array_equal(p.wordcount,arr1) and np.array_equal(q.wordcount,arr2)):
        raise ValueError('Filtered array not as expected.')

@test
def test_word_filters(c):
    arr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    brr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    arr1 = np.array([('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    arr2 = np.array([('a',1),('b',2)],dtype=config.DT_WORD_WEIGHT)
    p = Post('asd', wordcount=arr, client=c)
    p.filter_by_word(['c','d','e', 'f'], reverse=False)
    q = Post('def',wordcount=brr, client=c)
    q.filter_by_word(['c','d','e'], reverse=True)
    if not (np.array_equal(p.wordcount,arr1) and np.array_equal(q.wordcount,arr2)):
        raise ValueError('Filtered array not as expected.')

@test
def test_sorting(c):
    arr = np.array([('e',1),('a',2),('c',3),('b',4),('d',5)],dtype=config.DT_WORD_WEIGHT)
    brr = np.array([('a',2),('b',4),('c',3),('d',5),('e',1)],dtype=config.DT_WORD_WEIGHT)
    p = Post('asd',client=c, wordcount=arr)
    p.sort_by_word()
    if not np.array_equal(p.wordcount, brr):
        raise ValueError('Sorted array incorrect.')
    arr = np.array([('e',1),('a',2),('c',3),('b',4),('d',5)],dtype=config.DT_WORD_WEIGHT)
    brr = np.array([('a',2),('b',4),('c',3),('d',5),('e',1)],dtype=config.DT_WORD_WEIGHT)
    p = Post('asd',client=c, wordcount=brr)
    p.sort_by_weight()
    if not np.array_equal(p.wordcount, arr):
        raise ValueError('Sorted array incorrect.')

@test
def test_parallel_func(c):
    class myParallel(Parallel):
        def parallel_process(self, pkg, common):
            return pkg**2

    def callback(l):
        l.extend([n**2 for n in range(50)])

    square_list = []
    p = myParallel(range(50), nthreads=4)
    p.set_callback(func=callback, args=(square_list,))
    p.start()
    p.wait_for_threads()
    r = p.get_results()
    if not r==square_list:
        raise ValueError('Result list incorrect.')

@test
def test_query_class(c):
    q = Query(Query.GALLERY_HOT).sort_by(Query.TOP).over(Query.WEEK).construct()
    assert q.content == {'section':'hot', 'sort':'top', 'window':'week'}, \
                            'Not same as expected dict.'
    q = Query(Query.SUBREDDIT).params('news').sort_by(Query.TIME).construct()
    assert q.content == {'sort':'time', 'subreddit':'news'}, \
                            'Not same as expected dict.'
    q = Query(Query.MEMES).sort_by(Query.VIRAL).construct()
    assert q.content == {'sort':'viral'}, \
                            'Not same as expected dict.'
    try:
        q = Query(Query.SUBREDDIT).sort_by(Query.VIRAL).construct()
        raise Exception('InvalidArgument exception expected.')
    except config.InvalidArgument:
        pass
    try:
        q = Query(Query.TAG).sort_by(Query.RISING).construct()
        raise Exception('InvalidArgument exception expected.')
    except config.InvalidArgument:
        pass

@test
def test_parser_instance(c):
    P = Parser(client=c)

@test
def test_parser_population(c):
    global SAMPLE_PARSER
    SAMPLE_PARSER = Parser(client=c)
    q = Query(Query.GALLERY_USER).construct()
    SAMPLE_PARSER.get(q)                          # get Post objects from query
    assert len(SAMPLE_PARSER.items)>0, 'Query result of size 0.'

    global SAMPLE_POST
    userids = SAMPLE_POST.network
    SAMPLE_PARSER.populate_users(userids)

    global SAMPLE_USER
    SAMPLE_PARSER.populate_posts(SAMPLE_USER.posts)
    SAMPLE_PARSER.download()

@test
def test_parser_consolidation(c):
    arr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    brr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5), ('f', 6)],dtype=config.DT_WORD_WEIGHT)
    crr = np.array([('a',2),('b',4),('c',6),('d',8),('e',10), ('f', 6)],dtype=config.DT_WORD_WEIGHT)
    drr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5), ('f',0)],dtype=config.DT_WORD_WEIGHT)
    err = np.array([('a',1),('b',2),('c',3),('d',4),('e',5), ('f',6)],dtype=config.DT_WORD_WEIGHT)
    frr = np.array([('a',2),('b',4),('z',0)],dtype=config.DT_WORD_WEIGHT)
    grr = np.array([('a',1),('b',2),('z', 0)],dtype=config.DT_WORD_WEIGHT)
    p1 = Post(id=1,client=c,wordcount=arr)
    p2 = Post(id=2,client=c,wordcount=brr)
    P = Parser(client=c,items=(p1,p2))
    P.consolidate()
    assert np.array_equal(P.wordcount, crr), "Unexpected array output."
    assert np.array_equal(p1.wordcount, drr), "Unexpected array output."
    assert np.array_equal(p2.wordcount, err), "Unexpected array output."
    p1 = Post(id=1,client=c,wordcount=arr)
    p2 = Post(id=2,client=c,wordcount=brr)
    P = Parser(client=c,items=(p1,p2))
    P.consolidate(words=['a', 'b', 'z'], reverse=False)
    assert np.array_equal(P.wordcount, frr), "Unexpected array output."
    assert np.array_equal(p1.wordcount, grr), "Unexpected array output."
    assert np.array_equal(p2.wordcount, grr), "Unexpected array output."
    global SAMPLE_PARSER
    if SAMPLE_PARSER is None:
        raise ValueError('Depends on population test success.')
    for item in SAMPLE_PARSER.items:                    # so consolidation can work
        item.generate_word_counts(child_comments=True)
    SAMPLE_PARSER.consolidate()
    assert len(SAMPLE_PARSER.words), 'No wordcount generated.'

@test
def test_parser_baseline(c):
    global SAMPLE_PARSER
    a, v = SAMPLE_PARSER.get_baseline()
    assert len(a)==len(SAMPLE_PARSER.words) and len(a)==len(v),\
            'Incorrect output dimensions.'

@test
def test_parser_split(c):
    global SAMPLE_PARSER
    s1, s2 = SAMPLE_PARSER.split(0.6)
    assert len(s1) + len(s2) == len(SAMPLE_PARSER.items), \
            'Sample sizes do not add up.'

@test
def test_learner_instance(c):
    global SAMPLE_USER
    global SAMPLE_POST
    global SAMPLE_PARSER
    global SAMPLE_LEARNER
    SAMPLE_LEARNER = ()
    SAMPLE_LEARNER = Learner(source=SAMPLE_USER)
    SAMPLE_LEARNER = Learner(source=SAMPLE_PARSER) # does not check for type, just keyword
    SAMPLE_LEARNER = Learner(source=SAMPLE_PARSER)  # passed to the next func

@test
def test_learner_axes(c):
    global SAMPLE_PARSER
    global SAMPLE_USER
    global SAMPLE_LEARNER
    SAMPLE_LEARNER = Learner(source=SAMPLE_PARSER)
    _ = SAMPLE_LEARNER.get_axes()
    assert len(SAMPLE_LEARNER.axes)==len(SAMPLE_LEARNER.words) and isinstance(SAMPLE_LEARNER.axes, np.ndarray),\
                                'Axes not generated.'
    assert not np.any(np.iscomplex(SAMPLE_LEARNER.axes)), 'Complex axes found.'

    l = Learner(source=SAMPLE_USER)
    _ = l.get_comment_axes(child_comments=True)
    assert len(l.axes)==len(l.words) and isinstance(SAMPLE_LEARNER.axes, np.ndarray),\
                                'Axes not generated.'
    assert not np.any(np.iscomplex(l.axes)), 'Complex axes found.'

    l = Learner(source=SAMPLE_POST)
    _ = l.get_comment_axes()
    assert len(l.axes)==len(l.words) and isinstance(SAMPLE_LEARNER.axes, np.ndarray),\
                                'Axes not generated.'
    assert not np.any(np.iscomplex(l.axes)), 'Complex axes found.'

    myax1 = np.array([('a',1),('b',2),('c',3)], dtype=config.DT_WORD_WEIGHT)
    myax2 = np.array([('a',2),('b',4),('d',1)], dtype=config.DT_WORD_WEIGHT)
    _ = l.set_axes(axes=[myax1, myax2])
    assert len(l.axes)==len(l.words) and isinstance(SAMPLE_LEARNER.axes, np.ndarray),\
                                'Axes not generated.'
    p = Post(client=c, id='asd', wordcount=myax1)
    proj = l.project(p)
    assert len(proj[0,:])==len(l.axes[0,:]), 'Invalid projection to axes.'
    assert np.array_equal(proj[0,:], np.array([14,10])), 'Incorrect projection value.'

    l.save_axes('sample_axes.csv')
    m = Learner()
    m.load_axes('sample_axes.csv')
    os.remove('sample_axes.csv')
    assert np.array_equal(m.words, l.words), 'Loaded axes words do not match.'
    assert np.array_equal(m.axes, l.axes), 'Loaded axes do not match'

@test
def test_learner_projection(c):
    global SAMPLE_LEARNER
    global SAMPLE_POST
    if SAMPLE_LEARNER.axes is None:
        raise ValueError('Depends on learner axes test success.')
    proj = SAMPLE_LEARNER.project(SAMPLE_POST)
    assert len(proj)==1 and len(proj[0])==SAMPLE_LEARNER.axes.shape[1], \
                'Unexpected dimensions in result projections.'

@test
def test_learner_clustering(c):
    l = Learner()
    proj = np.array([[1,1,1],[1,2,3],[3,0,1],[2,0,0],[0,0,1],[0,1,0],[3,2,1],
                    [0,0,0],[2,1,2],[2,2,2],[3,2,3],[3,2,0],[1,1,0],[0,0,3]])
    centers, assignments = l.k_means_cluster(proj, 3)
    assert len(centers)==3 and len(assignments)==len(proj), \
            'Unequal dimensions to input data.'

    proj = np.arange(10)
    centers, assignments = l.k_means_cluster(proj, 3)
    assert len(centers)==3 and len(assignments)==len(proj), \
            'Unequal dimensions to input data.'

    centers = np.array([[1,0],[0,1],[-1,0]])
    proj = np.array([[0.5,0],[0,0.5],[-0.1,0],[5,0]])
    res = l.assign_to_cluster(proj, centers)
    assert np.array_equal(res, np.array([0,1,2,0])), 'Incorrect clustering.'

@test
def test_learner_regression(c):
    l = Learner()
    projections = np.array([1,2,3])
    predictions = np.array([2,4,6])
    res = l.linear_regression(projections, predictions)
    assert len(res)==2, 'Unexpected result dimensions'
    projections = np.array([[1,2,3],[5,4,6]])
    predictions = np.array([6, 15])
    res = l.linear_regression(projections, predictions)
    assert len(res)==4, 'Unexpected result dimensions'
    res2 = l.linear_prediction(np.array([[3,4,5]]))
    assert len(res2)==1 and res[0]+(3*res[1]+4*res[2]+5*res[3])==res2[0], \
                'Incorrect linear regression prediction.'

    proj = np.arange(10).reshape((5,2))
    lbl = np.array([0,0,0,1,1])
    res = l.logistic_regression(proj, lbl)
    assert res(np.array([0,1])) in [0,1], 'Wrong regression function.'
    proj = np.random.randint(0,100,size=(3,2))
    res = l.logistic_prediction(proj)
    assert len(res)==len(proj) and max(res)<=1 and min(res)>=0, \
            'Wrong logistic regression prediction.'

@test
def test_learner_decision_tree(c):
    l = Learner()
    data = np.array([[1,1,1],
                     [0,1,0],
                     [1,0,1],
                     [0,0,1],
                     [0,0,0],
                     [0,1,1],
                     [1,0,0],
                     [1,1,0]
                     ])
    labels = np.array([0,1,0,0,1,0,1,1])    # even numbers = 1
    dt = l.decision_tree(data, labels, branches=2)
    dt = l.decision_tree(data, labels, branches=[2,2,2])
    dt = l.decision_tree(data, labels, branches=[[0.5],[0.75],[0.9]])
    res = l.decision_prediction(np.array([[1,1,0]]))
    assert np.array_equal(res, np.array([[[1.,1.]]])), 'Incorrect decision.'
    dt = l.decision_tree(data, labels, branches=1)
    res = l.decision_prediction(np.array([[1,1,0]]))
    assert np.array_equal(res, np.array([[[0.,0.5],[1.,0.5]]])), 'Incorrect decision.'

@test
def test_bot_instance(c):
    global SAMPLE_BOT
    SAMPLE_BOT = Bot(client=c)

@test
def test_auth_url(c):
    b = Bot(client=c)
    url = b.auth_url
    r = requests.get(url)
    assert r.status_code==200, 'Could not validate auth url.'

@test
def test_bot_authentication(c):
    global SAMPLE_BOT
    if SAMPLE_BOT is None:
        raise Exception('Depends on Bot instance test success.')
    SAMPLE_BOT.load_credentials('testdata' + os.sep + 'sample.cred')
    assert SAMPLE_BOT.access_token=='ACCESS TOKEN' and SAMPLE_BOT.refresh_token=='REFRESH TOKEN',\
            'Credentials incorrrectly read.'
    if not os.path.exists('testdata' + os.sep + 'test.cred'):
        print('\nNew test run detected. Go to this link to get auth pin:\n' + SAMPLE_BOT.auth_url)
        try:
            pin = raw_input('Enter pin: ')
        except NameError:
            pin = input('Enter pin: ')
        SAMPLE_BOT.authorize(pin, credfile='testdata'+os.sep+'test.cred')
    else:
        SAMPLE_BOT.load_credentials('testdata'+os.sep+'test.cred')

@test
def test_bot_image_io(c):
    global SAMPLE_BOT
    res = SAMPLE_BOT.upload_image('testdata'+os.sep+'test.jpg', title='TEST')
    assert res.get('title')=='TEST', 'Image not uploaded.'
    SAMPLE_BOT.delete_image(res.get('id'))

@test
def test_bot_messaging(c):
    global SAMPLE_BOT
    n = SAMPLE_BOT.get_notifications(new=False, markread=False)
    assert ('messages' in n) and ('replies' in n), 'Unknown response format.'
    res = SAMPLE_BOT.post_comment('b91LE', 'test.py comment')
    assert 'id' in res, 'Comment not posted.'
    res = SAMPLE_BOT.client.delete_comment(res.get('id'))

@test
def test_bot_scheduler(c):
    global SAMPLE_BOT
    l = []
    def fill(obj):
        obj.append(1)
    SAMPLE_BOT.every(Bot.MINUTE/60).do(fill).using([l]).until(time.time()+3).go()
    time.sleep(3)
    SAMPLE_BOT.stop(force=True)
    assert len(l)==2 or len(l)==3, 'Unexpected scheduler timing result.'
    k = []
    SAMPLE_BOT.every(Bot.SECOND).do(fill).using([k]).times(2).go()
    time.sleep(3)
    SAMPLE_BOT.stop(force=False)
    assert len(k)==2, 'Unexpected scheduler frequency result.'

@test
def test_chatter(c):
    obj = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + 'testdata'+os.path.sep+'test_comment.object'
    with open(obj, 'rb') as f:
        comments = pickle.load(f)             # a serialized comment object w/ known values
    p = Post(client=c, id='xyz', comments=comments)
    c = Chatter(source = p)
    c.generate_chain()
    assert len(c.chain), 'Chain not generated.'
    res = c.random_comment()
    assert len(res), 'No output generated.'
    res = c.random_reply(to='here')
    assert len(res), 'No output generated.'

if __name__=='__main__':
    print('\n')
    if '-n' in sys.argv:
        get_test_data(c=CLIENT)

    print('Available API credits: ')
    print_credits()
    print('===============')
#   Post class only
    test_post_instance('Testing Post class instantiation:', c=CLIENT)
    test_post_download('Testing post data download:', c=CLIENT)
    test_post_user_extraction('Testing user id extraction from post:', c=CLIENT)

#   User class only
    test_user_instance('Testing User class instantiation:', c=CLIENT)
    test_user_download('Testing user data download:', c=CLIENT)
    test_user_post_extraction('Testing post id extraction from user:', c=CLIENT)

#   shared User/Post funcs
    test_sentence_sanitation('Testing sentence decomposition:', c=CLIENT)
    test_structure_flattening('Testing flattening nested comments:', c=CLIENT)
    test_word_counts('Testing word count generation:', c=CLIENT)
    test_normalization('Testing wordcount normalization:', c=CLIENT)
    test_weight_filters('Testing word count filters by weight:', c=CLIENT)
    test_word_filters('Testing word count filters by words:', c=CLIENT)
    test_parallel_func('Testing parallel execution:', c=CLIENT)
    test_sorting('Testing for wordcount sorting:', c=CLIENT)

#   Query class only
    test_query_class('Testing query construction:', c=CLIENT)

#   Parser class only
    test_parser_instance('Testing Parser class instantiation:', c=CLIENT)
    test_parser_population('Testing query, post, user population:', c=CLIENT)
    test_parser_consolidation('Testing for parser consolidation:', c=CLIENT)
    test_parser_baseline('Testing baseline generation:', c=CLIENT)
    test_parser_split('Testing item splitting for test/learn:', c=CLIENT)

#   Learner instance only
    test_learner_instance('Testing Learner class instantiation:', c=CLIENT)
    test_learner_axes('Testing eigenvector generation:', c=CLIENT)
    test_learner_projection('Testing projection to axes:', c=CLIENT)
    test_learner_clustering('Testing k-means clustering:', c=CLIENT)
    test_learner_regression('Testing learner regression:', c=CLIENT)
    test_learner_decision_tree('Testing decision tree: ', c=CLIENT)

#   Bot instance only
    test_bot_instance('Testing Bot class instantiation:', c=CLIENT)
    test_auth_url('Testing authentication URL:', c=CLIENT)
    test_bot_authentication('Testing Bot credentials:', c=CLIENT)
    test_bot_image_io('Testing image upload/delete:', c=CLIENT)
    test_bot_messaging('Testing bot messaging:', c=CLIENT)
    test_bot_scheduler('Testing Bot scheduler:', c=CLIENT)

#   Test macros
    test_chatter('Testing random chatter:', c=CLIENT)

    print('===============')
    print('Available API credits: ')
    print_credits()

    print('\n==================')
    print('Tests passed: ' + str(TESTS_PASSED))
    print('Tests failed: ' + str(TESTS_FAILED))
    print('==================\n')
