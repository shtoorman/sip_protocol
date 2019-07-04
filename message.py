class Message(object):
    _address = ['contact', 'from', 'record-route', 'refer-to', 'referred-by', 'route', 'to']
    _comma = ['authorization', 'proxy-authenticate', 'proxy-authorization', 'www-authenticate']
    _unstructured = ['call-id', 'cseq', 'date', 'expires', 'max-forwards', 'organization', 'server', 'subject',
                     'timestamp', 'user-agent']
    _short = ['allow-events', 'u', 'call-id', 'i', 'contact', 'm', 'content-encoding', 'e', 'content-length', 'l',
              'content-type', 'c', 'event',
              'o', 'from', 'f', 'subject', 's', 'supported', 'k', 'to', 't', 'via', 'v']
    _exception = {'call-id': 'Call-ID', 'cseq': 'CSeq', 'www-authenticate': 'WWW-Authenticate'}

    _quote = lambda s: '"' + s + '"' if s[0] != '"' != s[-1] else s
    _unquote = lambda s: s[1:-1] if s[0] == '"' == s[-1] else s

    _keywords = ['method', 'uri', 'response', 'responsetext', 'protocol', '_body', 'body']
    _single = ['call-id', 'content-disposition', 'content-length', 'content-type', 'cseq', 'date', 'expires', 'event',
               'max-forwards',
               'organization', 'refer-to', 'referred-by', 'server', 'session-expires', 'subject', 'timestamp', 'to',
               'user-agent']

    def _canon(s):
        s = s.lower()

        return ((len(s) == 1) and s in Message._short and Message._comma(
            Message._short[Message._short.index(s) - 1])) or (
                       s in Message._exception and Message._exception[s]) or '-'.join(
            [x.capitalize() for x in s.split('-')])

    # def quote( s):
    #         return lambda s: '"' + s + '"' if s[0] != '"' != s[-1] else s

    def __getattr__(self, name):
        return self.__getitem__(name)

    def __getattribute__(self, name):
        return object.__getattribute__(self, name.lower())

    def __setattr__(self, name, value):
        object.__setattr__(self, name.lower(), value)

    def __delattr__(self, name):
        object.__delattr__(self, name.lower())

    def __hasattr__(self, name):
        object.__hasattr__(self, name.lower())

    def __getitem__(self, name):
        return self.__dict__.get(name.lower(), None)

    def __setitem__(self, name, value):
        self.__dict__[name.lower()] = value

    def __contains__(self, name):
        return name.lower() in self.__dict__

#
# print(Message._canon('call-Id'))
# print(Message._canon('fRoM'))
# print(Message._canon('refer-to'))

