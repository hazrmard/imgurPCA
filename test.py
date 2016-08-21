from __future__ import print_function
from post import Post
import config
from imgurpython.helpers.error import ImgurClientError

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
def test_instance():
    p = Post(123, comments=['123', 'abc'], cs=config.CLIENT_SECRET, cid=config.CLIENT_ID)
    p = Post(123, comments=['123', 'abc'], cs='123fasfa', cid='asdeerwwe33')
    try:
        p = Post(123)
    except config.InvalidArgument:
        pass

@test
def test_download():
    p = Post('MScn5', cs=config.CLIENT_SECRET, cid=config.CLIENT_ID)
    p.download()
    try:
        p = Post('123', cs=config.CLIENT_SECRET, cid=config.CLIENT_ID)
        p.download()
    except ImgurClientError:
        pass

if __name__=='__main__':
    test_instance('Testing Post class instantiation:')
    test_download('Testing post data download:')

    print('\n')
