from __future__ import print_function
from post import Post
from user import User
import utils
import config
from imgurpython.helpers.error import ImgurClientError
import pickle

print('\n')

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
    p = Post('MScn5', cs=config.CLIENT_SECRET, cid=config.CLIENT_ID)
    p.download()
    try:
        p = Post('123', cs=config.CLIENT_SECRET, cid=config.CLIENT_ID)
        p.download()
    except ImgurClientError:
        pass

@test
def test_structure_flattening():
    """check if arbitrarily nested comments can be flattened for parsing"""
    with open('test_comment.object', 'rb') as f:
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
def test_user_instance():
    u = User('blah', cid='asdadasd', cs='123123qd')
    try:
        u = User(123)
    except config.InvalidArgument:
        pass


@test
def test_user_download():
    u = User('test', cid=config.CLIENT_ID, cs=config.CLIENT_SECRET)
    u.download()
    try:
        u = User('123', cs=config.CLIENT_SECRET, cid=config.CLIENT_ID)
        u.download()
    except ImgurClientError:
        pass

if __name__=='__main__':
    test_post_instance('Testing Post class instantiation:')     # Post class only
    test_post_download('Testing post data download:')


    test_user_instance('Testing User class instantiation:')     # User class only
    test_user_download('Testing user data download:')

    test_sentence_sanitation('Testing sentence decomposition:') # shared funcs
    test_structure_flattening('Testing flattening nested comments:')
    test_word_counts('Testing word count generation:')

    print('\n')
