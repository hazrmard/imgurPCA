__author__ = 'Ibrahim'

from imgurparse import ImgurParse

client_id = '***REMOVED***'
client_secret = '***REMOVED***'

imgurInstance = ImgurParse(client_id, client_secret)

imgurInstance.get().parse(parsechildren=False, cumulative=False).filter(num=1000).sort().truncate(1000, cumulative=True).consolidate().store().credits()

