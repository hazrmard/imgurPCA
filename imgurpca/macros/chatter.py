from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from ..base import Molecular
from ..base import Atomic
from ..base import Markov
import re

# The Chatter class privides an interface to generate random comments and replies
# from a Markov chain created from the source's plaintext.

class Chatter(Markov):

    @property
    def plaintext(self):
        if isinstance(self.source, Molecular):
            comments = self.source.content(flatten=False)
        else:
            comments = self.source.content
        text =  '\n'.join([c.comment for c in comments])
        text = re.sub(r'https?.+?\s', '', text)  # remove all urls
        return text


    def sanitize(self, text):
        return super(Chatter, self).sanitize(text)

    def random_comment(self):
        return self.sanitize(super(Chatter, self).random_walk())

    def random_reply(self, to):
        return self.sanitize(super(Chatter, self).random_walk(begin=to))


'''
def test():
    from imgurpca import Query, Parser
    from myconfig import CS, CID
    q=Query(Query.GALLERY_TOP).sort_by(Query.TOP).over(Query.DAY).construct()
    p=Parser(cs=CS, cid=CID)
    p.get(q)
    p.items = p.items[:5]
    p.download()
    c = Chatter(source=p, order=3)
    c.generate_chain()
    out = c.sanitize(c.random_walk(times=10))
    print(out)
    return c
'''
