__author__ = 'Ibrahim'

import time

def parse_url(url):
    """Returns components of a valid url as a dictionary.
       Can incorporate error checks more easily."""
    result = {'protocol': None, 'host': None, 'uri': None}
    temp = ''                           # constructs most recent URL component
    num_slash = 0                       # counts number of slashes
    for i in range(len(url)):                     # iterates over each character in URL
        #print url[i]
        if url[i] == ':':               # ':' marks end of protocol
            result['protocol'] = temp
            continue
        elif url[i] == '/':
            num_slash += 1              # keeping count of slashes
            if num_slash == 2:          # 2 slashes mark start of host
                temp = ''               # resetting temp to construct host
                continue
            elif num_slash == 3:        # 3 slashes mark end of host
                result['host'] = temp
                temp = ''               # resetting temp to construct uri
                continue
        temp += url[i]                  # constructs string from each char
    if num_slash == 2:                  # if only 2 slashes, then last temp construct = host
        result['host'] = temp
    else:                               # otherwise last temp construct = uri
        result['uri'] = temp

    return result


def parse_url2(url):
    """Returns components of a valid url as a dictionary.
       Faster by a factor of ~4 over 10,000 executions"""
    result = {}
    colon_index = url.find(':')       # colon marks end of protocol
    third_slash_index =  url[colon_index+3:len(url)].find('/')
    if third_slash_index != -1:                              # 3rd '/' marks end of host
        third_slash_index += colon_index + 3
    else:                                                    # no 3rd slash, host till end of url
        third_slash_index = len(url)
    result['protocol'] = url[0:colon_index]                  # protocol from start to ':'
    result['host'] = url[colon_index+3:third_slash_index]    # host is from ':'+3 to 3rd '/' or end of url
    result['uri'] = url[third_slash_index+1:len(url)]        # uri from 3rd '/' to end of url
    return result




print parse_url('https://www.google.com/maps')

a1 = time.clock()
for x in range(1000):
    parse_url('https://www.google.com/maps')
print time.clock() - a1

print parse_url2('https://www.google.com/maps')

a1 = time.clock()
for x in range(1000):
    parse_url2('https://www.google.com/maps')
print time.clock() - a1
