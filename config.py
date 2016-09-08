import numpy as np

DT_WORD_WEIGHT = np.dtype([('word', 'U32'), ('weight', float)])
DT_WORD = np.dtype([('word', 'U32')])
DT_WEIGHT = np.dtype([('weight', float)])

DEFAULT_WORD_WEIGHT = lambda post, comment, level: 1    # equal weight
DEFAULT_SORT_ORDER = 'word'

class InvalidArgument(Exception):
    pass

class PrematureFunctionCall(Exception):
    pass

class FunctionNotApplicable(Exception):
    pass
