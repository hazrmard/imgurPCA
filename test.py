from __future__ import print_function
from __future__ import unicode_literals
from post import Post
from user import User
from parse import Parser
from learn import Learner
from parallel import Parallel
from query import Query
from bot import Bot
import utils
import config
from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError
import pickle
import numpy as np
import os
import time
import sys
import requests

print('\n')

SAMPLE_POST = None
SAMPLE_USER = None
SAMPLE_PARSER = None
SAMPLE_LEARNER = None
SAMPLE_BOT = None

TESTS_PASSED = 0
TESTS_FAILED = 0

CLIENT_SECRET = ''
CLIENT_ID = ''

def get_test_data(cs, cid):
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

def print_credits(cs, cid):
    client = ImgurClient(cid,cs)
    credits = client.credits
    credits['UserReset'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(credits['UserReset']))
    [print(x[0]+': '+str(x[1]),end='; ') for x in credits.items()]
    print('\n')


@test
def test_post_instance(cs, cid):
    """check if instantiation of Post works with accentable arguments"""
    p = Post(123, comments=['123', 'abc'], cs=cs, cid=cid)
    p = Post(123, comments=['123', 'abc'], cs='123fasfa', cid='asdeerwwe33')
    try:
        p = Post(123)
        raise Exception('InvalidArgument expected.')
    except config.InvalidArgument:
        pass

@test
def test_post_download(cs, cid):
    """check if all post/comment/user data can be downloaded"""
    global SAMPLE_POST
    SAMPLE_POST = Post('b91LE', cs=cs, cid=cid)
    SAMPLE_POST.download()
    try:
        p = Post('123', cs=cs, cid=cid)
        p.download()
        raise Exception('ImgurClientError expected.')
    except ImgurClientError:
        pass

@test
def test_post_user_extraction(cs, cid):
    if SAMPLE_POST is None:
        raise ValueError('Depends on download test success.')
    ids = SAMPLE_POST.get_user_ids()
    assert isinstance(ids, (list,tuple)) and len(ids)>0 and isinstance(ids[0], basestring),\
            'ids non-list/tuple OR ids 0-length OR ids non-string'

@test
def test_user_instance(cs, cid):
    u = User('blah', cid='asdadasd', cs='123123qd')
    try:
        u = User(123)
        raise Exception('InvalidArgument exception expected.')
    except config.InvalidArgument:
        pass

@test
def test_user_download(cs, cid):
    global SAMPLE_USER
    SAMPLE_USER = User('apitester', cid=cid, cs=cs)
    SAMPLE_USER.download(pages=(0,100))
    try:
        u = User('123', cs=cs, cid=cid)
        u.download()
        raise Exception('ImgurClientError expected.')
    except ImgurClientError:
        pass

@test
def test_user_post_extraction(cs, cid):
    if SAMPLE_USER is None:
        raise ValueError('Depends on download test success.')
    ids = SAMPLE_USER.get_post_ids()
    assert isinstance(ids, (list,tuple)) and len(ids)>0 and isinstance(ids[0], basestring),\
            'ids non-list/tuple OR ids 0-length OR ids non-string'

@test
def test_structure_flattening(cs, cid):
    """check if arbitrarily nested comments can be flattened for parsing"""
    p = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + 'testdata' +\
                                                os.sep + 'test_comment.object'
    with open(p, 'rb') as f:
        comments = pickle.load(f)             # a serialized comment object w/ known values
    n=0
    for c in utils.flatten(comments):
        n+=1
    if n!=54:
        raise ValueError('Comment object incorrectly flattened.')

@test
def test_sentence_sanitation(cs, cid):
    """check if sentences can be correctly decomposed into words"""
    s = 'THE QuiCK !brOWn.'
    expected = ['the', 'quick', '!brown.']
    res = utils.sanitize(s)
    if res != expected:
        raise ValueError('Unexpected sentence decomposition.')

@test
def test_word_counts(cs, cid):
    """check if parsing funcs work w/ current imgur data structure"""
    obj = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + 'testdata'+os.path.sep+'test_comment.object'
    with open(obj, 'rb') as f:
        comments = pickle.load(f)             # a serialized comment object w/ known values
    p = Post('asd',cid='asd',cs='asd', comments=comments, points=100)
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
def test_weight_filters(cs, cid):
    arr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    brr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    arr1 = np.array([('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    arr2 = np.array([('a',1),('b',2)],dtype=config.DT_WORD_WEIGHT)
    p = Post('asd', wordcount=arr, cs='123',cid='asd')
    p.filter_by_weight(3,5)
    q = Post('def',wordcount=brr, cs='123',cid='asd')
    q.filter_by_weight(3,5,True)
    if not (np.array_equal(p.wordcount,arr1) and np.array_equal(q.wordcount,arr2)):
        raise ValueError('Filtered array not as expected.')

@test
def test_word_filters(cs, cid):
    arr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    brr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    arr1 = np.array([('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    arr2 = np.array([('a',1),('b',2)],dtype=config.DT_WORD_WEIGHT)
    p = Post('asd', wordcount=arr, cs='123',cid='asd')
    p.filter_by_word(['c','d','e'], reverse=False)
    q = Post('def',wordcount=brr, cs='123',cid='asd')
    q.filter_by_word(['c','d','e'], reverse=True)
    if not (np.array_equal(p.wordcount,arr1) and np.array_equal(q.wordcount,arr2)):
        raise ValueError('Filtered array not as expected.')

@test
def test_sorting(cs, cid):
    arr = np.array([('e',1),('a',2),('c',3),('b',4),('d',5)],dtype=config.DT_WORD_WEIGHT)
    brr = np.array([('a',2),('b',4),('c',3),('d',5),('e',1)],dtype=config.DT_WORD_WEIGHT)
    p = Post('asd',cid='asd',cs='asd', wordcount=arr)
    p.sort_by_word()
    if not np.array_equal(p.wordcount, brr):
        raise ValueError('Sorted array incorrect.')
    arr = np.array([('e',1),('a',2),('c',3),('b',4),('d',5)],dtype=config.DT_WORD_WEIGHT)
    brr = np.array([('a',2),('b',4),('c',3),('d',5),('e',1)],dtype=config.DT_WORD_WEIGHT)
    p = Post('asd',cid='asd',cs='asd', wordcount=brr)
    p.sort_by_weight()
    if not np.array_equal(p.wordcount, arr):
        raise ValueError('Sorted array incorrect.')

@test
def test_parallel_func(cs, cid):
    class myParallel(Parallel):
        def parallel_process(self, pkg, common):
            return pkg**2

    p = myParallel(range(50),nthreads=4)
    p.start()
    p.wait_for_threads()
    r = p.get_results()
    if not r==[n**2 for n in range(50)]:
        raise ValueError('Result list incorrect.')

@test
def test_query_class(cs, cid):
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
def test_parser_instance(cs, cid):
    P = Parser(cid=cid, cs=cs)

@test
def test_parser_population(cs, cid):
    global SAMPLE_PARSER
    SAMPLE_PARSER = Parser(cid=cid, cs=cs)
    q = Query(Query.GALLERY_USER).construct()
    SAMPLE_PARSER.get_posts(q)                          # get Post objects from query
    assert len(SAMPLE_PARSER.items)>0, 'Query result of size 0.'

    global SAMPLE_POST
    userids = SAMPLE_POST.network
    SAMPLE_PARSER.populate_users(userids)

    global SAMPLE_USER
    postids = SAMPLE_USER.network[:5]
    SAMPLE_PARSER.populate_posts(postids)
    SAMPLE_PARSER.download()

@test
def test_parser_consolidation(cs, cid):
    arr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5)],dtype=config.DT_WORD_WEIGHT)
    brr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5), ('f', 6)],dtype=config.DT_WORD_WEIGHT)
    crr = np.array([('a',2),('b',4),('c',6),('d',8),('e',10), ('f', 6)],dtype=config.DT_WORD_WEIGHT)
    drr = np.array([('a',1),('b',2),('c',3),('d',4),('e',5), ('f',0)],dtype=config.DT_WORD_WEIGHT)
    err = np.array([('a',1),('b',2),('c',3),('d',4),('e',5), ('f',6)],dtype=config.DT_WORD_WEIGHT)
    p1 = Post(id=1,cs='123',cid='123',wordcount=arr)
    p2 = Post(id=2,cs='123',cid='123',wordcount=brr)
    P = Parser(cid='123',cs='123',items=(p1,p2))
    P.consolidate()
    assert np.array_equal(P.wordcount, crr), "Unexpected array output."
    assert np.array_equal(p1.wordcount, drr), "Unexpected array output."
    assert np.array_equal(p2.wordcount, err), "Unexpected array output."
    global SAMPLE_PARSER
    if SAMPLE_PARSER is None:
        raise ValueError('Depends on population test success.')
    for item in SAMPLE_PARSER.items:                    # so consolidation can work
        item.generate_word_counts(child_comments=True)
    SAMPLE_PARSER.consolidate()

@test
def test_parser_baseline(cs, cid):
    global SAMPLE_PARSER
    a, v = SAMPLE_PARSER.get_baseline()
    assert len(a)==len(SAMPLE_PARSER.words) and len(a)==len(v),\
            'Incorrect output dimensions.'

@test
def test_parser_split(cs, cid):
    global SAMPLE_PARSER
    s1, s2 = SAMPLE_PARSER.split(0.6)
    assert len(s1.items) + len(s2.items) == len(SAMPLE_PARSER.items), \
            'Sample sizes do not add up.'

@test
def test_learner_instance(cs, cid):
    global SAMPLE_USER
    global SAMPLE_POST
    global SAMPLE_PARSER
    global SAMPLE_LEARNER
    SAMPLE_LEARNER = ()
    SAMPLE_LEARNER = Learner(user=SAMPLE_USER)
    SAMPLE_LEARNER = Learner(user=SAMPLE_PARSER) # does not check for type, just keyword
    SAMPLE_LEARNER = Learner(parser=SAMPLE_PARSER)  # passed to the next func

@test
def test_learner_axes(cs, cid):
    global SAMPLE_PARSER
    global SAMPLE_USER
    global SAMPLE_LEARNER
    SAMPLE_LEARNER = Learner(parser=SAMPLE_PARSER)
    _ = SAMPLE_LEARNER.get_axes()
    assert len(SAMPLE_LEARNER.axes)==len(SAMPLE_LEARNER.words) and isinstance(SAMPLE_LEARNER.axes, np.ndarray),\
                                'Axes not generated.'
    assert not np.any(np.iscomplex(SAMPLE_LEARNER.axes)), 'Complex axes found.'

    l = Learner(user=SAMPLE_USER)
    _ = l.get_comment_axes(child_comments=True)
    assert len(l.axes)==len(l.words) and isinstance(SAMPLE_LEARNER.axes, np.ndarray),\
                                'Axes not generated.'
    assert not np.any(np.iscomplex(l.axes)), 'Complex axes found.'

    l = Learner(user=SAMPLE_POST)
    _ = l.get_comment_axes()
    assert len(l.axes)==len(l.words) and isinstance(SAMPLE_LEARNER.axes, np.ndarray),\
                                'Axes not generated.'
    assert not np.any(np.iscomplex(l.axes)), 'Complex axes found.'

    myax1 = np.array([('a',1),('b',2),('c',3)], dtype=config.DT_WORD_WEIGHT)
    myax2 = np.array([('a',2),('b',4),('d',1)], dtype=config.DT_WORD_WEIGHT)
    _ = l.set_axes(axes=[myax1, myax2])
    assert len(l.axes)==len(l.words) and isinstance(SAMPLE_LEARNER.axes, np.ndarray),\
                                'Axes not generated.'

    l.save_axes('sample_axes.csv')
    m = Learner()
    m.load_axes('sample_axes.csv')
    os.remove('sample_axes.csv')
    assert np.array_equal(m.words, l.words), 'Loaded axes words do not match.'
    assert np.array_equal(m.axes, l.axes), 'Loaded axes do not match'

@test
def test_learner_projection(cs, cid):
    global SAMPLE_LEARNER
    global SAMPLE_POST
    if SAMPLE_LEARNER.axes is None:
        raise ValueError('Depends on learner axes test success.')
    proj = SAMPLE_LEARNER.project(SAMPLE_POST)
    assert len(proj)==1 and len(proj[0])==SAMPLE_LEARNER.axes.shape[1], \
                'Unexpected dimensions in result projections.'

@test
def test_learner_clustering(cs, cid):
    l = Learner()
    proj = np.array([[1,1,1],[1,2,3],[3,0,1],[2,0,0],[0,0,1],[0,1,0],[3,2,1],
                    [0,0,0],[2,1,2],[2,2,2],[3,2,3],[3,2,0],[1,1,0],[0,0,3]])
    centers, assignments = l.k_means_cluster(proj, 3)
    assert len(centers)==3 and len(assignments)==len(proj), \
            'Unequal dimensions to input data.'

    centers = np.array([[1,0],[0,1],[-1,0]])
    proj = np.array([[0.5,0],[0,0.5],[-0.1,0],[5,0]])
    res = l.assign_to_cluster(proj, centers)
    assert np.array_equal(res, np.array([0,1,2,0])), 'Incorrect clustering.'

@test
def test_bot_instance(cs, cid):
    global SAMPLE_BOT
    SAMPLE_BOT = Bot(cs=cs, cid=cid)

@test
def test_auth_url(cs, cid):
    b = Bot(cs=cs, cid=cid)
    url = b.auth_url()
    r = requests.get(url)
    assert r.status_code==200, 'Could not validate auth url.'

@test
def test_bot_authentication(cs, cid):
    global SAMPLE_BOT
    if SAMPLE_BOT is None:
        raise Exception('Depends on Bot instance test success.')
    SAMPLE_BOT.load_credentials('testdata' + os.sep + 'sample.cred')
    assert SAMPLE_BOT.access_token=='ACCESS TOKEN' and SAMPLE_BOT.refresh_token=='REFRESH TOKEN',\
            'Credentials incorrrectly read.'
    if not os.path.exists('testdata' + os.sep + 'test.cred'):
        print('\nNew test run detected. Go to this link to get auth pin:\n' + SAMPLE_BOT.auth_url())
        try:
            pin = raw_input('Enter pin: ')
        except NameError:
            pin = input('Enter pin: ')
        SAMPLE_BOT.authorize(pin, credfile='testdata'+os.sep+'test.cred')
    else:
        SAMPLE_BOT.load_credentials('testdata'+os.sep+'test.cred')

@test
def test_bot_image_io(cs, cid):
    global SAMPLE_BOT
    res = SAMPLE_BOT.upload_image('testdata'+os.sep+'test.jpg', title='TEST')
    assert res.get('title')=='TEST', 'Image not uploaded.'
    SAMPLE_BOT.delete_image(res.get('id'))

@test
def test_bot_scheduler(cs, cid):
    global SAMPLE_BOT
    l = []
    def fill(obj):
        obj.append(1)
    SAMPLE_BOT.every(Bot.MINUTE/60).do(fill).using([l]).until(time.time()+3).go()
    time.sleep(3)
    assert len(l)==2 or len(l)==3, 'Unexpected scheduler result'

if __name__=='__main__':
    if '-n' in sys.argv:
        get_test_data(cs=CLIENT_SECRET, cid=CLIENT_ID)

    print('Available API credits: ')
    print_credits(cid=CLIENT_ID, cs=CLIENT_SECRET)
    print('===============')
#   Post class only
    test_post_instance('Testing Post class instantiation:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_post_download('Testing post data download:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_post_user_extraction('Testing user id extraction from post:', cs=CLIENT_SECRET, cid=CLIENT_ID)

#   User class only
    test_user_instance('Testing User class instantiation:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_user_download('Testing user data download:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_user_post_extraction('Testing post id extraction from user:', cs=CLIENT_SECRET, cid=CLIENT_ID)

#   shared User/Post funcs
    test_sentence_sanitation('Testing sentence decomposition:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_structure_flattening('Testing flattening nested comments:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_word_counts('Testing word count generation:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_weight_filters('Testing word count filters by weight:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_word_filters('Testing word count filters by words:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_parallel_func('Testing parallel execution:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_sorting('Testing for wordcount sorting:', cs=CLIENT_SECRET, cid=CLIENT_ID)

#   Query class only
    test_query_class('Testing query construction:', cs=CLIENT_SECRET, cid=CLIENT_ID)

#   Parser class only
    test_parser_instance('Testing Parser class instantiation:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_parser_population('Testing query, post, user population:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_parser_consolidation('Testing for parser consolidation:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_parser_baseline('Testing baseline generation:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_parser_split('Testing item splitting for test/learn:', cs=CLIENT_SECRET, cid=CLIENT_ID)

#   Learner instance only
    test_learner_instance('Testing Learner class instantiation:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_learner_axes('Testing eigenvector generation:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_learner_projection('Testing projection to axes:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_learner_clustering('Testing k-means clustering:', cs=CLIENT_SECRET, cid=CLIENT_ID)

#   Bot instance only
    test_bot_instance('Testing Bot class instantiation:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_auth_url('Testing authentication URL:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_bot_authentication('Testing Bot credentials:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_bot_image_io('Testing image upload/delete:', cs=CLIENT_SECRET, cid=CLIENT_ID)
    test_bot_scheduler('Testing Bot scheduler:', cs=CLIENT_SECRET, cid=CLIENT_ID)

    print('===============')
    print('Available API credits: ')
    print_credits(cid=CLIENT_ID, cs=CLIENT_SECRET)

    print('\n==================')
    print('Tests passed: ' + str(TESTS_PASSED))
    print('Tests failed: ' + str(TESTS_FAILED))
    print('==================\n')
