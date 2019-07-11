from message import Message
from address import Address
from url import URI


class Header(object):
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

    @staticmethod
    def _canon(s):
        s = s.lower()
        return ((len(s) == 1) and s in Header._short and Header._canon(Header._short[Header._short.index(s) - 1])) \
               or (s in Header._exception and Header._exception[s]) or '-'.join([x.capitalize() for x in s.split('-')])

    def _parse(self, value, name):
        if name in Header._address:  # address header
            addr = Address()
            addr.mustQuote = True
            count = addr.parse(value)
            value, rest = addr, value[count:]
            if rest:
                for n, sep, v in map(lambda x: x.partition('='), rest.split(';') if rest else []):
                    if n.strip():
                        self.__dict__[n.lower().strip()] = v.strip()
        elif name not in Header._comma and name not in Header._unstructured:  # standard
            value, sep, rest = value.partition(';')
            for n, sep, v in map(lambda x: x.partition('='), rest.split(';') if rest else []):
                self.__dict__[n.lower().strip()] = v.strip()

        if name in Header._comma:
            self.authMethod, sep, rest = value.strip().partition(' ')
            for n, v in map(lambda x: x.strip().split('='), rest.split(',') if rest else []):
                self.__dict__[n.lower().strip()] = Header._unquote(v.strip())

        elif name == 'cseq':
            n, sep, self.method = map(lambda x: x.strip(), value.partition(' '))
            self.number = int(n)
            value = n + ' ' + self.method
        return value

    def __init__(self, value=None, name=None):
        self.name = name and Header._canon(name.strip()) or None
        self.value = self._parse(value.strip(), self.name and self.name.lower() or None)

    def __str__(self):
        name = self.name.lower()

        rest = '' if ((name in Header._comma) or (name in Header._unstructured)) \
            else (';'.join(map(lambda x: self.__dict__[x] and '%s=%s' % (x.lower(), self.__dict__[x]) or x,
                               filter(lambda x: x.lower() not in ['name', 'value', '_viauri'],
                                      self.__dict__))))
        return str(self.value) + (rest and (';' + rest) or '')

    def __repr__(self):
        return self.name + ": " + str(self)

    def dup(self):
        return Header(self.__str__(), self.name)

    def __getitem__(self, name):
        return self.__dict__.get(name.lower(), None)

    def __setitem__(self, name, value):
        self.__dict__[name.lower()] = value

    def __contains__(self, name):
        return name.lower() in self.__dict__

    @property
    def viaUri(self):
        if not hasattr(self, '_viaUri'):
            if self.name != 'Via':
                raise ValueError

        proto, addr = self.value.split(' ')
        type = proto.split('/')[2].lower()  # udp, tcp, tls
        self._viaUri = URI('sip:' + addr + ';transport=' + type)
        if self._viaUri.port == None:
            self._viaUri.port = 5060
        if 'rport' in self:
            try:
                self._viaUri.port = int(self.rport)
            except:
                pass  # probably not an int
        if type not in ['tcp', 'sctp', 'tls']:
            if 'maddr' in self:
                self._viaUri.host = self.maddr
        elif 'received' in self:
            self._viaUri.host = self.received
        return self._viaUri

    @staticmethod
    def createHeaders(value):
        name, value = map(str.strip, value.split(':', 1))

        return (Header._canon(name),
                map(lambda x: Header(x, name), value.split(',') if name.lower() not in Message._comma else [value]))


# a = Header('SIP/2.0/UDP example.net:5090;ttl=1', 'Via')
# print(a.name)
# print(a.value)
# print(a.viaUri)
# print(Header('SIP/2.0/UDP 192.1.2.3;rport=1078;received=76.17.12.18;branch=0', 'Via').viaUri)
# #
# print(Header('SIP/2.0/UDP 192.1.2.3;maddr=224.0.1.75', 'Via').viaUri)
# print(Header._canon('call_id'))
# print(Header._canon('fRoM'))
# print(Header._canon('refer-to'))
print(Header.createHeaders('Event: presence, reg'))
print(repr(Header('"Kundan Singh" <sip:kundan@example.net>', 'To')))
#To: "Kundan Singh" <sip:kundan@example.net>
print(repr(Header('"Kundan"<sip:kundan99@example.net>', 'To')))
#To: "Kundan" <sip:kundan99@example.net>
print(repr(Header('Sanjay <sip:sanjayc77@example.net>', 'fRoM')))
#From: "Sanjay" <sip:sanjayc77@example.net>
print(repr(Header('application/sdp', 'conTenT-tyPe')))

print(repr(Header('presence; param=value;param2=another', 'Event')))
#Event: presence;param=value;param2=another
print(repr(Header('78 INVITE', 'CSeq')))