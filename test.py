from __future__ import print_function
from __future__ import unicode_literals
from post import Post
from user import User
from parse import Parser
from parallel import Parallel
from query import Query
import utils
import config
from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError
import pickle
import numpy as np
import os
import time

print('\n')

SAMPLE_POST = None
SAMPLE_USER = None

TESTS_PASSED = 0
TESTS_FAILED = 0

CLIENT_SECRET = ''
CLIENT_ID = ''

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
    SAMPLE_POST = Post('ozfNx', cs=cs, cid=cid)
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
    SAMPLE_USER.download()
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
    p = Parser(cid=cid, cs=cs)
    q = Query(Query.GALLERY_USER).construct()
    p.get_posts(q)                          # get Post objects from query

    global SAMPLE_POST
    userids = SAMPLE_POST.network[:2]
    p.populate_users(userids)

    global SAMPLE_USER
    postids = SAMPLE_USER.network[:2]
    p.populate_posts(postids)
    p.download()

if __name__=='__main__':
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

    print('===============')
    print('Available API credits: ')
    print_credits(cid=CLIENT_ID, cs=CLIENT_SECRET)

    print('\n==================')
    print('Tests passed: ' + str(TESTS_PASSED))
    print('Tests failed: ' + str(TESTS_FAILED))
    print('==================\n')
