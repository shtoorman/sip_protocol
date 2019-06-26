class Message(object):
    _address = ['contact', 'from', 'record-route', 'refer-to', 'referred-by', 'route', 'to']
    _comma = ['authorization', 'proxy-authenticate', 'proxy-authorization', 'www-authenticate']
    _unstructured = ['call-id', 'cseq', 'date', 'expires', 'max-forwards', 'organization', 'server', 'subject',
                     'timestamp', 'user-agent']
    _short = ['allow-events', 'u', 'call-id', 'i', 'contact', 'm', 'content-encoding', 'e', 'content-length', 'l',
              'content-type', 'c', 'event',
              'o', 'from', 'f', 'subject', 's', 'supported', 'k', 'to', 't', 'via', 'v']
    _exception = {'call-id': 'Call-ID', 'cseq': 'CSeq', 'www-authenticate': 'WWW-Authenticate'}

    def _canon(s):
        s = s.lower()

    # a = ((len(s) == 1) and s in _short and _canon(_short[_short.index(s) - 1]))
    # print(a)
        return (((len(s) == 1) and s in _short and _comma(_short[_short.index(s) - 1])) or (
            s in _exception and _exception[s]) or '-'.join([x.capitalize() for x in s.split('-')]))
