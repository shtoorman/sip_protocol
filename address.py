import re
from url import URI
import socket
import struct


class Address(object):
    _syntax = [re.compile('^(?P<name>[a-zA-Z0-9\-\.\_\+\~\ \t]*)<(?P<uri>[^>]+)>'),
               re.compile('^(?:"(?P<name>[a-zA-Z0-9\-\.\_\+\~\ \t]+)")[\ \t]*<(?P<uri>[^>]+)>'),
               re.compile('^[\ \t]*(?P<name>)(?P<uri>[^;]+)', )]

    def parse(self, value):
        if str(value).startswith('*'):
            self.wildcard = True
            return 1
        else:
            for s in Address._syntax:
                m = s.match(value)
                if m:
                    self.displayName = m.groups()[0].strip()
                    self.uri = URI(m.groups()[1].strip())
                    return m.end()

    def __init__(self, value=None):
        self.displayName = self.uri = None
        self.wildcard = self.mustQuote = False
        if value:
            self.parse(value)

    def __repr__(self):
        return (('"' + self.displayName + '"' + (' ' if self.uri else '')) if self.displayName else '') \
               + ((('<' if self.mustQuote or self.displayName else '')
                   + repr(self.uri)
                   + ('>' if self.mustQuote or self.displayName else '')) if self.uri else '')

    def dup(self):
        return Address(self.__repr__())

    @property
    def displayable(self):
        name = self.displayName or self.uri and self.uri.user or self.uri and self.uri.host or ''
        return name if len(name) < 25 else (name[0:22] + '...')

    @staticmethod
    def isIPv4(data):
        try:
            m = socket.inet_aton(data)
            return True
        except:
            return False

    @staticmethod
    def isMulticast(data):
        try:
            m, = struct.unpack('>/', socket.inet_aton(data))
            return ((m & 0xF0000000) == 0xE0000000)  # class D: 224.0.0.0/4 or first four bits as 0111
        except:
            return False


# a1 = Address('"Aleksandr Balandin" <sip:shtoorman@example.net>')
# a2 = Address('Aleksandr Balandin <sip:shtoorman@example.net>')
# a3 = Address('"Aleksandr Balandin" <sip:kundan@example.net> ')
# a4 = Address('<sip:shtoorman@example.net>')
# a5 = Address('sip:shtoorman@example.net')

# print(str(a1) == str(a2) and str(a1) == str(a3) and str(a1.uri) == str(a4.uri) and str(a1.uri) == str(a5.uri))
# print(a1)
# print(a1.displayable)
# print("isIPv4 {} ".format(Address.isIPv4('10.2.3.4.45')))
print(Address.isMulticast('224.0.1.2') is True)
print(False is Address.isMulticast('10.2.3.4'))
print(Address.isIPv4('10.2.3.4') is True)
print(False is Address.isIPv4('10.2.3.a') == Address.isIPv4('10.2.3.a.5') == Address.isIPv4('10.2.3.-2') == Address.isIPv4('10.2.3.403'))
