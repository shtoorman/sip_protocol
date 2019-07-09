import random
import ipaddress
from url import URI
from header import Header
from message import Message


class Stack(object):

    def __init__(self, app, transport):

        self.tag = str(random.randint(0, 2 ** 31))
        self.app, self.transport = app, transport
        self.closing = False
        self.dialogs, self.transactions = dict(), dict()
        self.serverMethods = ['INVITE', 'BYE', 'MESSAGE', 'SUBSCRIBE', 'NOTIFY']

    def __del__(self):
        self.closing = True
        for d in self.dialogs: del self.dialogs[d]
        for t in self.transactions: del self.transactions[t]
        del self.dialogs
        del self.transactions

    @property
    def uri(self):
        transport = self.transport
        return URI(((transport.type == 'tls') and 'sips' or 'sip') + ':' + transport.host + ':' + str(transport.port))

    @property
    def newCallId(self):
        return str(random.randint(0, 2 ** 31)) + '@' + (self.transport.host or 'localhost')

    def createVia(self, secure=False):
        if not self.transport:
            raise ValueError('No transport in stack')

        if secure and not self.transport.secure:
            raise ValueError('Cannot find a secure transport')
        return Header('SIP/2.0/' + self.transport.type.upper() + ' ' + self.transport.host + ':' + str(
            self.transport.port) + ';rport', 'Via')

    def send(self, data, dest=None, transport=None):
        if dest and isinstance(dest, URI):
            if not uri.host:
                raise ValueError('No host in destination uri')
            dest = (dest.host, dest.port or self.transport.type == 'tls' and self.transport.secure and 5061 or 5060)
        if isinstance(data, Message):
            if data.method:  # request
                if dest and ipaddress.is_multicast(dest[0]):
                    data.first('Via')['maddr'], data.first('Via')['ttl'] = dest[0], 1
        elif data.response:  # response
            if not dest:
                dest = data.first('Via').viaUri.hostPort
        self.app.send(str(data), dest, stack=self)

    def received(self, data, src):
        try:
            m = Message(data)
            uri = URI((self.transport.secure and 'sips' or 'sip') + ':' + str(src[0]) + ':' + str(src[1]))
            if m.method:
                # additional checks on request
                self._receivedRequest(m, uri)
            elif m.response:
                self._receivedResponse(m, uri)
            else:
                raise ValueError('Received invalid message')
        except ValueError:
            if _debug:
                print('Error in received message:')
        if m.Via == None:
            raise ValueError('No Via header in request')
        via = m.first('Via')
        if via.viaUri.host != src[0] or via.viaUri.port != src[1]:
            via['received'], via.viaUri.host = src[0], src[0]
        if 'rport' in via:
            via['rport'] = src[1]
            via.viaUri.port = src[1]

    def _receivedRequest(self, r, uri):
        branch = r.first('Via').branch

        if r.method == 'ACK' and branch == '0':
            t = None
        else:
            t = self.findTransaction(Transaction.createId(branch, r.method))

        if not t:
            app = None
        else:
            t.receivedRequest(r)

        if r.method != 'CANCEL' and 'tag' in r.To:
            ...  # process an in-dialog request
        elif r.method != 'CANCEL':
            ...  # process out-of-dialog request
        else:
            ...  # process a CANCEL request
        if app:
            t = Transaction.createServer(self, app, r, self.transport, self.tag)
        elif r.method != 'ACK':
            self.send(Message.createResponse(404, "Not found", None, None, r))


















def createServer(self, request, uri, stack):
    return UserAgent(stack, request) if request.method != “REGISTER” else None


def receivedRequest(self, ua, request, stack): ...


def receivedResponse(self, ua, response, stack): ...


def sending(self, ua, message, stack): ...


def cancelled(self, ua, request, stack): ...


def dialogCreated(self, dialog, ua, stack): ...


def authenticate(self, ua, obj, stack):
    obj.username, obj.password = "shtoorman", "mysecret"
    return True


def createTimer(self, app, stack):
    return Timer(app)
