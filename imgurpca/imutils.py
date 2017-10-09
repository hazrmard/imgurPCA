# for any utility functions that apply strictly to the imgur API and not generally
# to parsing/learning etc.
import time
from argparse import Action
from imgurpython import ImgurClient
from . import config
from . import Query

def set_up_client(instance, **kwargs):
    """sets up self.client with ImgurClient instance given either client secret
    and client id or an ImgurClient instance.
    Raises InvalidArgument if ('cs' and 'cid') or 'client' keyword args not present.
    """
    if 'cid' in kwargs and 'cs' in kwargs:
        instance.client = ImgurClient(kwargs['cid'], kwargs['cs'])
    elif 'client' in kwargs:
        instance.client = kwargs['client']
    else:
        raise config.InvalidArgument('Either include client=ImgurClient()'
                            ' instance, or cid=CLIENT_ID and cs=CLIENT_SECRET')


class QueryParser(Action):
    """
    Parses query string passed by a command line option. Of the form:
        --<OPT> <WHAT> [FunctionName1:Argument] [FunctionName2:Argument] ....
    Where OPT is the option name. Must be prefixed by '-' characters.
    Where WHAT is the instantiation argument to Query() class.
    Where FunctionName is one of Query.[sort_by, over, params], and Argument
    is the argument passed to it. For example:
        gallery_top over:day sort_by:hot
    Passed to argparse.ArgumentParser().add_argument(action=) when parsing
    query from the command line.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        query = Query(getattr(Query, values[0].upper()))
        for val in values[1:]:
            func, arg = val.split(':')
            getattr(query, func.lower())(arg)
        if option_string is None:
            setattr(namespace, 'query', query.construct())
        else:
            setattr(namespace, option_string.replace('-', ''), query.construct())


def get_credits(client):
    credits = client.credits
    try:
        credits['UserReset'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(credits['UserReset']))
    except TypeError:
        pass
    return credits
