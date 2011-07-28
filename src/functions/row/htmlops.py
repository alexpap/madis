# coding: utf-8
import urllib
import re
from htmlentitydefs import name2codepoint
name2codepoint['#39'] = 39
import urlparse
import os
import mimetypes
import xml.sax.saxutils
import operator
import json

def urlsplit(*args):

    """
    .. function:: urlsplit(text1, [text2,...]) -> multiset

    Breaks a given URL into multiple fields. The returned table schema is:

    :scheme: What type the URL is (e.g. http, ftp ...)
    :netloc: Network location of URL (e.g. www.text.com)
    :path: Path part of URL (e.g. /data/2010/). It always has a slash at the end
    :filename: Filename part of URL
    :type: Mime type of URL, or if not a mime type exists, the extension part of filename.
    :subtype: Mime subtype of URL.
    :params: All parameters following ';' in URL.
    :query: All parameters following '?' in URL.
    :fragment: All parameters following '#' in URL.

    Examples:

    >>> table1('''
    ... http://www.test.com/apath/bpath/fname.pdf
    ... http://www.test.com/search.csv;p=5?q=test#hl=en
    ... ''')
    >>> sql("select urlsplit(a) from table1")
    scheme | netloc       | path          | filename   | type        | subtype | params | query  | fragment
    -------------------------------------------------------------------------------------------------------
    http   | www.test.com | /apath/bpath/ | fname.pdf  | application | pdf     |        |        |
    http   | www.test.com | /             | search.csv | csv         |         | p=5    | q=test | hl=en
    """

    yield ('scheme', 'netloc', 'path', 'filename', 'type', 'subtype', 'params', 'query', 'fragment')

    url=''.join(args)
    u=urlparse.urlparse(''.join(args))
    pf=os.path.split(u[2])

    if len(pf)==2:
        path, filename=pf
    else:
        path, filename=pf[0], ''

    if len(path)>0 and path[-1]!='/':
        path+='/'

    m=mimetypes.guess_type(url)
    if m[0]!=None:
        m1, m2=m[0].split('/')
    else:
        m1, m2=(os.path.splitext(filename)[1], '')
        if len(m1)>0 and m1[0]=='.':
            m1=m1[1:]

    yield [u[0], u[1], path, filename, m1, m2, u[3], u[4], u[5]]

urlsplit.registered=True
urlsplit.multiset=True

def urllocation(*args):

    """
    .. function:: urllocation(str) -> str

    Returns the location part of provided URL.

    Examples:

    >>> table1('''
    ... http://www.test.com/apath/bpath/fname.pdf
    ... http://www.test.com/search.csv;p=5?q=test#hl=en
    ... ''')
    >>> sql("select urllocation(a) from table1")
    urllocation(a)
    -----------------------------------------
    http://www.test.com/apath/bpath/fname.pdf
    http://www.test.com/search.csv
    """

    u=urlparse.urlparse(''.join(args))

    return u[0]+u'://'+''.join(u[1:3])

urllocation.registered=True

def urlquerysplit(*args):

    """
    .. function:: urlquerysplit(URL or URL_query_part) -> [multiple fields]

    Splits the query part of a URL into multiple fields.

    Examples:

    >>> table1('''
    ... 'url_ver=ver1&url_tim=2011-01-01T00%3A02%3A40Z'
    ... 'url_tim=2011-01-01T00%3A02%3A40Z&url_ver=ver1'
    ... http://www.test.com/search.csv;p=5?url_tim=test&url_ver=en
    ... ''')
    >>> sql("select urlquerysplit(a) from table1")
    url_tim              | url_ver
    ------------------------------
    2011-01-01T00:02:40Z | ver1
    2011-01-01T00:02:40Z | ver1
    en                   | test
    """

    url=args[0]
    if url.startswith('http://'):
        url=urlparse.urlparse(url)[4]
    u=urlparse.parse_qsl(url, True)

    u.sort(key=operator.itemgetter(1,0))

    yield tuple([x[0] for x in u])
    yield [x[1] for x in u]
    
urlquerysplit.registered=True

def urlquerytojdict(*args):
    """
    .. function:: urlquerytojdict(str) -> [multiple fields]

    Converts the query part of a URL into a JSON associative array.

    Examples:

    >>> table1('''
    ... 'url_ver=ver1&url_tim=2011-01-01T00%3A02%3A40Z'
    ... 'url_tim=2011-01-01T00%3A02%3A40Z&url_ver=ver1'
    ... http://www.test.com/search.csv;p=5?lang=test&ver=en
    ... ''')
    >>> sql("select urlquerytojdict(a) from table1")
    urlquerytojdict(a)
    ---------------------------------------------------
    {"url_tim":"2011-01-01T00:02:40Z","url_ver":"ver1"}
    {"url_tim":"2011-01-01T00:02:40Z","url_ver":"ver1"}
    {"lang":"test","ver":"en"}
    """

    url=args[0]
    if url.startswith('http://'):
        url=urlparse.urlparse(url)[4]
    u=urlparse.parse_qs(url, True)

    for x,y in u.iteritems():
        if len(y)==1:
            u[x]=y[0]

    return json.dumps(u, separators=(',',':'), ensure_ascii=False)

urlquerytojdict.registered=True

def htmlunescape(s):
    return re.sub('&(%s);' % '|'.join(name2codepoint),
              lambda m: unichr(name2codepoint[m.group(1)]), s)

def htmldecode(*args):
    """
    .. function:: htmldecode(str)

    Returns the html decoded *str*.

    Examples:

    >>> sql("select htmldecode('(&quot;die+wunderbaren+jahre&quot;)') as query")
    query
    -------------------------
    ("die+wunderbaren+jahre")
    >>> sql("select htmldecode(null) as query")
    query
    -----
    None
    """
    if len(args)>1:
        raise functions.OperatorError("htmldecode","operator takes only one argument")
    if args[0]==None:
        return None
    return htmlunescape(args[0])

htmldecode.registered=True

def htmlencode(*args):
    """
    .. function:: htmldecode(str)

    Returns the html decoded *str*.

    Examples:

    >>> sql("select htmldecode('(&quot;die+wunderbaren+jahre&quot;)') as query")
    query
    -------------------------
    ("die+wunderbaren+jahre")
    >>> sql("select htmldecode(null) as query")
    query
    -----
    None
    """
    if len(args)>1:
        raise functions.OperatorError("htmldecode","operator takes only one argument")
    if args[0]==None:
        return None

    return xml.sax.saxutils.escape(u''.join(args[0]), {'"': "&quot;"})

htmlencode.registered=True

def urldecode(*args):
    """
    .. function:: urldecode(str)

    Returns the url decoded *str*.

    Examples:

    >>> sql("select urldecode('where%2Ccollid%3Dcolid+and+u%3D%27val%27') as query")
    query
    ------------------------------
    where,collid=colid and u='val'


    >>> sql("select urldecode(null) as query")
    query
    -----
    None
    """
    if len(args)>1:
        raise functions.OperatorError("urldecode","operator takes only one argument")
    if args[0]!=None:
        return unicode(urllib.unquote_plus(args[0]))
    return None

urldecode.registered=True

def urlencode(*args):
    """
    .. function:: urlescape(str)

    Returns the escaped URL.

    Examples:

    >>> sql("select urlencode('where, collid=colid') as query")
    query
    -----------------------
    where%2C+collid%3Dcolid

    """
    if len(args)>1:
        raise functions.OperatorError("urlencode","operator takes only one argument")
    if args[0]!=None:
        return urllib.quote_plus(unicode(args[0]))
    return None

urlencode.registered=True

addwbr=re.compile(r'([./-])([^./\-\d\s])', re.DOTALL| re.UNICODE)

def htmladdbreaks(*args):
    """
    .. function:: url(href, linktext)

    Returns the a url pointing to *href* and having the link text *linktext*.

    Examples:

    >>> sql("select htmladdbreaks('very-long/string') as brokenhtml")
    brokenhtml
    --------------------------
    very-<wbr>long/<wbr>string
    """

    if args[0]==None:
        return None

    out=u''.join([unicode(x) for x in args])

    return addwbr.sub(r'\1<wbr>\2', out)

htmladdbreaks.registered=True

def htmllink(*args):
    """
    .. function:: htmllink(href, linktext)

    Returns the an html link pointing to *href* and having the link text *linktext*.

    Examples:

    >>> sql("select htmllink('http://somewhere.org') as url") #doctest:+ELLIPSIS +NORMALIZE_WHITESPACE
    url
    -----------------------------------------------------------------
    <a href="http://somewhere.org">http://<wbr>somewhere.<wbr>org</a>

    >>> sql("select htmllink('somewhere.org') as url")
    url
    -----------------------------------------------------
    <a href="http://somewhere.org">somewhere.<wbr>org</a>

    >>> sql("select htmllink('somewhere.org', 'go somewhere') as url")
    url
    -----------------------------------------------
    <a href="http://somewhere.org">go somewhere</a>

    """
    def addhttp(u):
        if u.find('://')==-1:
            return u'http://'+unicode(u)
        return unicode(u)

    if len(args)>2:
        raise functions.OperatorError("url","operator a maximum of two arguments")

    if len(args)==2:    
        if args[1]!=None:
            return '<a href="'+addhttp(args[0])+'">'+unicode(args[1])+'</a>'

    if args[0]==None:
        return None
    return '<a href="'+addhttp(args[0])+'">'+htmladdbreaks(htmlencode(unicode(args[0])))+'</a>'

htmllink.registered=True

if not ('.' in __name__):
    """
    This is needed to be able to test the function, put it at the end of every
    new function you create
    """
    import sys
    import setpath
    from functions import *
    testfunction()
    if __name__ == "__main__":
        reload(sys)
        sys.setdefaultencoding('utf-8')
        import doctest
        doctest.testmod()
