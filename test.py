from __future__ import print_function
from __future__ import unicode_literals
from post import Post
from user import User
from parse import Parser
from parallel import Parallel
import utils
import config
from imgurpython.helpers.error import ImgurClientError
import pickle
import numpy as np
import os

print('\n')

SAMPLE_POST = None
SAMPLE_USER = None

def test(fn):
    def wrapper(*args, **kwargs):
        print(args[0])
        try:
            fn(*args[1:], **kwargs)
            print('\tSUCCESS')
        except Exception as e:
            print('\tFAULURE - ' + str(e))
        print()
    return wrapper


@test
def test_post_instance():
    """check if instantiation of Post works with accentable arguments"""
    p = Post(123, comments=['123', 'abc'], cs=config.CLIENT_SECRET, cid=config.CLIENT_ID)
    p = Post(123, comments=['123', 'abc'], cs='123fasfa', cid='asdeerwwe33')
    try:
        p = Post(123)
    except config.InvalidArgument:
        pass

@test
def test_post_download():
    """check if all post/comment/user data can be downloaded"""
    global SAMPLE_POST
    SAMPLE_POST = Post('ozfNx', cs=config.CLIENT_SECRET, cid=config.CLIENT_ID)
    SAMPLE_POST.download()
    try:
        p = Post('123', cs=config.CLIENT_SECRET, cid=config.CLIENT_ID)
        p.download()
    except ImgurClientError:
        pass

@test
def test_post_user_extraction():
    if SAMPLE_POST is None:
        raise ValueError('Depends on download test success.')
    ids = SAMPLE_POST.get_user_ids()
    assert(isinstance(ids, (list,tuple)) and len(ids)>0 and isinstance(ids[0], basestring))

@test
def test_user_instance():
    u = User('blah', cid='asdadasd', cs='123123qd')
    try:
        u = User(123)
    except config.InvalidArgument:
        pass

@test
def test_user_download():
    global SAMPLE_USER
    SAMPLE_USER = User('apitester', cid=config.CLIENT_ID, cs=config.CLIENT_SECRET)
    SAMPLE_USER.download()
    try:
        u = User('123', cs=config.CLIENT_SECRET, cid=config.CLIENT_ID)
        u.download()
    except ImgurClientError:
        pass

@test
def test_user_post_extraction():
    if SAMPLE_USER is None:
        raise ValueError('Depends on download test success.')
    ids = SAMPLE_USER.get_post_ids()
    assert(isinstance(ids, (list,tuple)) and len(ids)>0 and isinstance(ids[0], basestring))

@test
def test_structure_flattening():
    """check if arbitrarily nested comments can be flattened for parsing"""
    p = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + 'test_comment.object'
    with open(p, 'rb') as f:
        comments = pickle.load(f)             # a serialized comment object w/ known values
    n=0
    for c in utils.flatten(comments):
        n+=1
    if n!=54:
        raise ValueError('Comment object incorrectly flattened.')

@test
def test_sentence_sanitation():
    """check if sentences can be correctly decomposed into words"""
    s = 'THE QuiCK !brOWn.'
    expected = ['the', 'quick', '!brown.']
    res = utils.sanitize(s)
    if res != expected:
        raise ValueError('Unexpected sentence decomposition.')

@test
def test_word_counts():
    """check if parsing funcs work w/ current imgur data structure"""
    p = Post('MScn5', cs=config.CLIENT_SECRET, cid=config.CLIENT_ID)
    p.download()
    p.generate_word_counts(child_comments=False, comment_votes=True,
                            comment_level=True)
    p.generate_word_counts(child_comments=False, comment_votes=True,
                            comment_level=False)
    p.generate_word_counts(child_comments=True, comment_votes=True,
                            comment_level=True)
    u = User('test', cid=config.CLIENT_ID, cs=config.CLIENT_SECRET)
    u.download()
    u.generate_word_counts()

@test
def test_weight_filters():
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
def test_word_filters():
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
def test_sorting():
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
def test_parallel_func():
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
def test_parser_instance():
    P = Parser(cid=config.CLIENT_ID, cs=config.CLIENT_SECRET)

if __name__=='__main__':
#   Post class only
    test_post_instance('Testing Post class instantiation:')
    test_post_download('Testing post data download:')
    test_post_user_extraction('Testing user id extraction from post:')

#   User class only
    test_user_instance('Testing User class instantiation:')
    test_user_download('Testing user data download:')
    test_user_post_extraction('Testing post id extraction from user:')

#   shared User/Post funcs
    test_sentence_sanitation('Testing sentence decomposition:')
    test_structure_flattening('Testing flattening nested comments:')
    test_word_counts('Testing word count generation:')
    test_weight_filters('Testing word count filters by weight:')
    test_word_filters('Testing word count filters by words:')
    test_parallel_func('Testing parallel execution:')
    test_sorting('Testing for wordcount sorting:')

#   Parser class only
    test_parser_instance('Testing Parser class instantiation:')

    print('\n')
