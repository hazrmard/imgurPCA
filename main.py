__author__ = 'Ibrahim'

from imgurparse import imgurparse

client_id = '***REMOVED***'
client_secret = '***REMOVED***'

imgurInstance = imgurparse(client_id, client_secret)

imgurInstance.get().parse(parsechildren=False, cumulative=False).filter(num=1000).truncate(1000).sort().store().credits()

