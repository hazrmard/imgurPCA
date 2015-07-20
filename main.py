__author__ = 'Ibrahim'

import imgurAPI

client_id = '***REMOVED***'
client_secret = '***REMOVED***'

imgurInstance = imgurAPI.imgurAPI(client_id, client_secret)

imgurInstance.gallery_retrieval('hot', 'top', 'day')
imgurInstance.comment_parse()

