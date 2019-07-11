from url import URI


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

        #str.21