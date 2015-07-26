__author__ = 'Ibrahim'

import imgurAPI

client_id = '***REMOVED***'
client_secret = '***REMOVED***'

imgurInstance = imgurAPI.imgurAPI(client_id, client_secret)

imgurInstance.get().parse(parsechildren=False).filter(num=1000).store().credits()

