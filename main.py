__author__ = 'Ibrahim'

import imgurAPI

client_id = '***REMOVED***'
client_secret = '***REMOVED***'

imgurInstance = imgurAPI.imgurAPI(client_id, client_secret)

imgurInstance.get().parse(parsechildren=False, cumulative=False).filter(num=1000).truncate(1000).sort().store().credits()

