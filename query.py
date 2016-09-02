from __future__ import unicode_literals
from config import InvalidArgument, PrematureFunctionCall


class Query(object):

    # what
    GALLERY_TOP = 0     # search main gallery: top section
    GALLERY_HOT = 1     # search main gallery: hot section
    GALLERY_USER = 2    # search main gallery: user submitted section
    SUBREDDIT = 3       # search particular subreddit
    MEMES = 4           # search memes subgallery
    TAG = 5             # search items with particular tag
    CUSTOM = 6          # provide custom search terms
    RANDOM = 7          # generate random gallery items
    _allowed_whats = (GALLERY_TOP, GALLERY_USER, GALLERY_HOT, SUBREDDIT, MEMES,
                        TAG, CUSTOM, RANDOM)

    # sort by
    TIME = 'time'       # allowed in: GALLERY_*, SUBREDDIT, MEMES, TAG, CUSTOM
    VIRAL = 'viral'     # allowed in: GALLERY_*, MEMES, TAG, CUSTOM
    TOP = 'top'         # allowed in: GALLERY_*, SUBREDDIT, MEMES, TAG, CUSTOM
    RISING = 'rising'   # allowed in: GALLERY_USER
    _allowed_sorts = (TIME, VIRAL, TOP, RISING)

    # over (only applicable when sort by: top)
    DAY = 'day'
    WEEK = 'week'
    MONTH = 'month'
    YEAR = 'year'
    ALL = 'all'
    _allowed_overs = (DAY, WEEK, MONTH, YEAR, ALL)


    def __init__(self, what):
        """select what to query
        @param what (int): one of Query.GALLERY_TOP, Query.GALLERY_HOT,
                    Query.GALLERY_USER, Query.SUBREDDIT, Query.MEMES, Query.TAG,
                    Query.CUSTOM, Query.RANDOM
        """
        if not what in Query._allowed_whats:
            raise InvalidArgument('''Choose from Query.GALLERY_TOP, Query.GALLERY_HOT,
                        Query.GALLERY_USER, Query.SUBREDDIT, Query.MEMES, Query.TAG,
                        Query.CUSTOM, Query.RANDOM''')
        self._what = what
        self._sort_by = Query.VIRAL
        self._over = Query.DAY          # == window in API
        self._q = ""                    # custom search parameter
        self._q_params = None           # compiled parameters

    def over(self, ovr):
        """period to query over. Only applies if sort by: top
        @param ovr (str): one of Query.DAY, Query.WEEK, Query.MONTH, Query.YEAR,
                            Query.ALL
        """
        if not ovr in Query._allowed_overs:
            raise InvalidArgument('Choose from Query.DAY, Query.WEEK, Query.MONTH, Query.YEAR,\
                                Query.ALL')
        self._over = ovr
        return self


    def sort_by(self, sort):
        """sorting criterion/section to query.
        @param sort (str): one of One of Query.TOP, Query.TIME, Query.RISING, Query.VIRAL
        """
        if not sort in Query._allowed_sorts:
            raise InvalidArgument('Choose from Query.TOP, Query.TIME,\
                                        Query.RISING, Query.VIRAL')
        self._sort_by = sort
        return self


    def params(self, q):
        """set the params for a Query.CUSTOM search
        @param p (str): a query string as defined by the API docs
        """
        if not self._what == Query.CUSTOM:
            raise PrematureFunctionCall('Query must me instantiated with Query.CUSTOM')
        self._q = q
        return self


    def construct(self):
        """compile choices into a dict/string query to be passed to Parser
        """
        params = {}
        self._q_params = (self._what, params)
        if self._what == Query.CUSTOM:              # set up custom query
            params['q'] = self._q
        if self._what == Query.RANDOM:              # random needs no query params
            return

        if self._sort_by == Query.TOP:              # window only if Query.TOP
            params['window'] = self._over
                                                    # process sort_bys:
        if self._what == Query.GALLERY_USER:        # accepts all sort_bys
            params['sort'] = self._sort_by
            return
        elif (self._what in (Query.GALLERY_TOP, Query.GALLERY_HOT, Query.SUBREDDIT,    # for TIME, TOP
                            Query.TAG, Query.MEMES, Query.CUSTOM)) and \
                            (self._sort_by in (Query.TIME, Query.TOP)):
            params['sort'] = self._sort_by
            return
        elif (self._what in (Query.GALLERY_TOP, Query.GALLERY_HOT, Query.TAG,         # for VIRAL
                        Query.MEMES, Query.CUSTOM)) and (self._sort_by==Query.VIRAL):
            params['sort'] = self._sort_by
            return
