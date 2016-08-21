import numpy as np

CLIENT_ID = '***REMOVED***'
CLIENT_SECRET = '***REMOVED***'

DT_WORD_COUNT = np.dtype([('word', unicode), ('count', int)])
DT_WORD_WEIGHT = np.dtype([('word', unicode), ('weight', float)])

DEFAULT_WORD_WEIGHT = lambda post, comment, level: 1

class InvalidArgument(Exception):
    pass

class PrematureFunctionCall(Exception):
    pass
