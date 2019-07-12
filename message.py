from url import URI
from header import Header


class Message(object):

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

    _keywords = ['method', 'uri', 'response', 'responsetext', 'protocol', '_body', 'body']
    _single = ['call-id', 'content-disposition', 'content-length', 'content-type', 'cseq', 'date', 'expires', 'event',
               'max-forwards',
               'organization', 'refer-to', 'referred-by', 'server', 'session-expires', 'subject', 'timestamp', 'to',
               'user-agent']

    def _parse(self, value):
        firstline, headers, body = value.split('\r\n\r\n', 1)
        a, b, c = firstline.split('', 2)
        try:  # try as response
            self.response, self.responsetext, self.protocol = int(b), c, a  # throws error if b is not int.
        except:  # probably a request
            self.method, self.uri, self.protocol = a, URI(b), c

        for h in headers.split('\r\n'):
            if h.startswith(r'[ \t]'):
                pass
                # parse the header line
                # str.21
                try:
                    name, values = Header.createHeaders(h)
                    if name not in self:  # doesn't already exist
                        self[name] = values if len(values) > 1 else values[0]
                    elif name not in Message._single:  # valid multiple-instance header
                        if not isinstance(self[name], list):
                            self[name] = self[name]
                        self[name] += values
                except:
                    continue

        bodyLen = int(self['Content-Length'].value) if 'Content-Length' in self else 0
        if body:
            self.body = body
        if self.body != None and bodyLen != len(body):
            raise ValueError('Invalid content-length %d!=%d')
        for h in ['To', 'From', 'CSeq', 'Call-ID']:
            if h not in self:
                raise ValueError('Mandatory header %s missing')

    def __init__(self, value=None):
        self.method = self.uri = self.response = self.responsetext = self.protocol = self._body = None

        if value:
            self._parse(value)

    def __repr__(self):
        if self.method != None:
            m = self.method + ' ' + str(self.uri) + ' ' + self.protocol + '\r\n'
        elif self.response != None:
            m = self.protocol + ' ' + str(self.response) + ' ' + self.responsetext + '\r\n'
        else:
            return None  # invalid message

        for h in self:
            m += repr(h) + '\r\n'
        m += '\r\n'
        if self.body != None:
            m += self.body
        return m

    def dup(self):
        return Message(self.__repr__())

    def __iter__(self):
        h = list()
        for n in filter(lambda x: not x.startswith('_') and x not in Message._keywords, self.__dict__):
            h += filter(lambda x: isinstance(x, Header), self[n] if isinstance(self[n], list) else [self[n]])
        return iter(h)

    def first(self, name):
        result = self[name]
        return isinstance(result, list) and result[0] or result

    def all(self, *args):
        args = map(lambda x: x.lower(), args)
        h = list()
        for n in filter(lambda x: x in args and not x.startswith('_') and x not in Message._keywords, self.__dict__):
            h += filter(lambda x: isinstance(x, Header), self[n] if isinstance(self[n], list) else [self[n]])
        return h

    def insert(self, header, append=False):
        if header and header.name:
            if header.name not in self:
                self[header.name] = header
            elif isinstance(self[header.name], Header):
                self[header.name] = (append and [self[header.name], header] or [header, self[header.name]])
            else:
                if append:
                    self[header.name].append(header)
                else:
                    self[header.name].insert(0, header)

    def body():
        def fset(self, value):
            self._body = value
            self['Content-Length'] = Header('%d' % (value and len(value) or 0), 'Content-Length')

        def fget(self):
            return self._body

        return locals()

    body = property(**body())

    for x in range(1, 7):
        exec
        'def is%dxx(self): return self.response and (self.response / 100 == %d)' % (x, x)
    exec
    'is%dxx = property(is%dxx)' % (x, x)

    @property
    def isfinal(self):
        return self.response and (self.response >= 200)

    @staticmethod
    def _populateMessage(m, headers=None, content=None):
        if headers:
            for h in headers: m.insert(h, True)  # append the header instead of overriding
        if content:
            m.body = content
        else:
            m['Content-Length'] = Header('0', 'Content-Length')

    @staticmethod
    def createRequest(method, uri, headers=None, content=None):
        m = Message()

        m.method, m.uri, m.protocol = method, URI(uri), 'SIP/2.0'
        Message._populateMessage(m, headers, content)
        if m.CSeq != None and m.CSeq.method != method:
            m.CSeq = Header(str(m.CSeq.number) + ' ' + method, 'CSeq')
        return m

    @staticmethod
    def createResponse(response, responsetext, headers=None, content=None, r=None):
        m = Message()
        m.response, m.responsetext, m.protocol = response, responsetext, 'SIP/2.0'
        if r:
            m.To, m.From, m.CSeq, m['Call-ID'], m.Via = r.To, r.From, r.CSeq, r['Call-ID'], r.Via
        if response == 100:
            m.Timestamp = r.Timestamp
        Message._populateMessage(m, headers, content)
        return m

##sip stack
