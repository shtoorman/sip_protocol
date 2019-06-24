import re


class URL(object):
    _syntax = re.compile('^(?P<scheme>[a-zA-Z][a-zA-Z0-9\+\-\.]*):'  # scheme
                         + '(?:(?:(?P<user>[a-zA-Z0-9\-\_\.\!\~\*\'\(\)&=\+\$,;\?\/\%]+)'  # user
                         + '(?::(?P<password>[^:@;\?]+))?)@)?'  # password
                         + '(?:(?:(?P<host>[^;\?:]*)(?::(?P<port>[\d]+))?))'  # host, port
                         + '(?:;(?P<params>[^\?]*))?'  # parameters
                         + '(?:\?(?P<headers>.*))?$')  # headers

    def __init__(self, value=''):
        m = URL._syntax.match(value)

        if not m:
            raise ValueError('Invalid URI({})' + value)

        self.scheme, self.user, self.password, self.host, self.port, params, headers = m.groups()

        if self.scheme == 'tel' and self.user is None:
            self.user, self.host = self.host, None

        self.port = self.port and int(self.port) or None

        self.header = [nv for nv in headers.split('&')] if headers else []

        splits = map(lambda n: n.partition('='), params.split(';')) if params else []
        self.param = dict(map(lambda k: (k[0], k[2] if k[2] else None), splits)) if splits else {}

        if value:
            ...  # parsing code

        else:
            self.scheme = self.user = self.password = self.host = self.port = None
            self.param = {}
            self.header = []

    def cmp(a, b):
        return (a > b) - (a < b)

    def __repr__(self):
        user, host = (self.user, self.host) if self.scheme != 'tel' else (None, self.user)

        return (self.scheme + ':' + ((user +
                                      ((':' + self.password) if self.password else '') + '@') if user else '') +
                (((host if host else '') + ((':' + str(self.port)) if self.port else '')) if host else '') +
                ((';' + ';'.join([(n + '=' + v if v is not None else n) for n, v in self.param.items()])) if len(
                    self.param) > 0 else '') +
                (('?' + '&'.join(self.header)) if len(self.header) > 0 else '')) if self.scheme and host else ''

    def dup(self):
        return URL(self.__repr__())

    @property
    def hostPort(self):
        return (self.host, self.port)

    def _ssecure(self, value):
        if value and self.scheme in ['sip', 'http']:
            self.scheme += 's'

    def _gsecure(self):
        return True if self.scheme in ['sips', 'https'] else False

    secure = property(fget=_gsecure, fset=_ssecure)


print(URL('sip:kundan@example.net'))
print(URL('sip:kundan:passwd@example.net:5060;transport=udp;lr?name=value&another=another'))
print(URL('sip:192.1.2.3:5060'))
print(URL("sip:kundan@example.net") == URL("sip:Kundan@Example.NET"))
print('empty=', URL())
print(URL('tel:+1-212-9397063'))
print(URL('sip:kundan@192.1.2.3:5060').hostPort)
