import numpy as np

CLIENT_ID = '***REMOVED***'
CLIENT_SECRET = '***REMOVED***'

DT_WORD_COUNT = np.dtype([('word',str), ('count',int)])
DT_WORD_WEIGHT = np.dtype([('word',str), ('weight',int)])

class InvalidArgument(Exception):
    pass

class PrematureFunctionCall(Exception):
    pass
