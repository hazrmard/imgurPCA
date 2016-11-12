from __future__ import unicode_literals
import numpy as np

# numpy does not play well with unicode literals, so appending b'to strings'
ENCODING = 'utf-8'
MAX_WORD_LENGTH = 32
DT_WORD = np.dtype([('word', str('U') + str(MAX_WORD_LENGTH))])
DT_WEIGHT = np.dtype([('weight', float)])
DT_WORD_WEIGHT = np.dtype(DT_WORD.descr + DT_WEIGHT.descr)

DEFAULT_WORD_WEIGHT = lambda post, comment, level: 1    # equal weight
DEFAULT_SORT_ORDER = str('word')

class InvalidArgument(Exception):
    pass

class PrematureFunctionCall(Exception):
    pass

class FunctionNotApplicable(Exception):
    pass
