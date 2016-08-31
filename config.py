import numpy as np

CLIENT_ID = '***REMOVED***'
CLIENT_SECRET = '***REMOVED***'

DT_WORD_COUNT = np.dtype([('word', 'U32'), ('count', int)])
DT_WORD_WEIGHT = np.dtype([('word', 'U32'), ('weight', float)])

DEFAULT_WORD_WEIGHT = lambda post, comment, level: 1    # equal weight

class InvalidArgument(Exception):
    pass

class PrematureFunctionCall(Exception):
    pass
