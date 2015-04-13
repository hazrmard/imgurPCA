__author__ = 'Ibrahim'

import imgurAPI

idlist = imgurAPI.gallery_retrieval('hot', 'top', 'day')
imgurAPI.comment_parse(idlist, False)

