import random
from url import URI
from header import Header
from message import Message
from address import Address

import random

class Stack(object):
    '''The SIP stack is associated with transport layer and controls message
    flow among different layers.

    The application must provide an app instance with following signature:
    class App():
        def send(self, data, dest): pass
            'to send data (str) to dest ('192.1.2.3', 5060).'
        def sending(self, data, dest): pass
            'to indicate that a given data (Message) will be sent to the dest (host, port).'
        def createServer(self, request, uri): return UserAgent(stack, request)
            'to ask the application to create a UAS for this request (Message) from source uri (Uri).'
        def receivedRequest(self, ua, request): pass
            'to inform that the UAS or Dialog has recived a new request (Message).'
        def receivedResponse(self, ua, request): pass
            'to inform that the UAC or Dialog has recived a new response (Message).'
        def cancelled(self, ua, request): pass
            'to inform that the UAS or Dialog has received a cancel for original request (Message).'
        def dialogCreated(self, dialog, ua): pass
            'to inform that the a new Dialog is created from the old UserAgent.'
        def authenticate(self, ua, header): header.password='mypass'; return True
            'to ask the application for credentials for this challenge header (Header).'
        def createTimer(self, cbObj): return timerObject
            'the returned timer object must have start() and stop() methods, a delay (int)
            attribute, and should invoke cbObj.timedout(timer) when the timer expires.'
    Only the authenticate and sending methods are optional. All others are mandatory.

    The application must invoke the following callback on the stack:
    stack.received(data, src)
        'when incoming data (str) received on underlying transport from
        src ('192.2.2.2', 5060).'

    The application must provide a Transport object which is an object with
    these attributes: host, port, type, secure, reliable, congestionControlled, where
        host: a string representing listening IP address, e.g., '192.1.2.3'
        port: a int representing listening port number, e.g., 5060.
        type: a string of the form 'udp', 'tcp', 'tls', or 'sctp' indicating the transport type.
        secure: a boolean indicating whether this is secure or not?
        reliable: a boolean indicating whether the transport is reliable or not?
        congestionControlled: a boolean indicating whether the transport is congestion controlled?
    '''
    def __init__(self, app, transport, fix_nat=False):
        '''Construct a stack using the specified application (higher) layer and
        transport (lower) data.'''
        self.tag = str(random.randint(0,2**31))
        self.app, self.transport, self.fix_nat = app, transport, fix_nat
        self.closing = False
        self.dialogs, self.transactions = dict(), dict()
        self.serverMethods = ['INVITE','BYE','MESSAGE','SUBSCRIBE','NOTIFY']
    def __del__(self):
        self.closing = True
        for d in self.dialogs: del self.dialogs[d]
        for t in self.transactions: del self.transactions[t]
        del self.dialogs; del self.transactions

    @property
    def uri(self):
        '''Construct a URI for the transport.'''
        transport = self.transport
        return URI(((transport.type == 'tls') and 'sips' or 'sip') + ':' + transport.host + ':' + str(transport.port))

    @property
    def newCallId(self):
        return str(uuid.uuid1()) + '@' + (self.transport.host or 'localhost')

    def createVia(self, secure=False):
        if not self.transport:
            raise ValueError('No transport in stack')
        if secure and not self.transport.secure:
            raise ValueError('Cannot find a secure transport')
        return Header('SIP/2.0/' + self.transport.type.upper() + ' ' + self.transport.host + ':' + str(self.transport.port) + ';rport', 'Via')

    def send(self, data, dest=None, transport=None):
        '''Send a data (Message) to given dest (URI or hostPort), or using the Via header of
        response message if dest is missing.'''
        # TODO: why do we need transport argument?
        if dest and isinstance(dest, URI):
            if not dest.host:
                raise ValueError('No host in destination uri')
            dest = (dest.host, dest.port or self.transport.type == 'tls' and self.transport.secure and 5061 or 5060)
        if isinstance(data, Message):
            if data.method:      # request
                # @implements RFC3261 P143L14-P143L19
                if dest and isMulticast(dest[0]):
                    data.first('Via')['maddr'], data.first('Via')['ttl'] = dest[0], 1
            elif data.response: # response: use Via if dest missing
                if not dest:
                    dest = data.first('Via').viaUri.hostPort
        self.app.send(str(data), dest, stack=self)

    def received(self, data, src):
        '''Callback when received some data (str) from the src ('host', port).'''
        m = Message()
        try:
            m._parse(data)
            uri = URI((self.transport.secure and 'sips' or 'sip') + ':' + str(src[0]) + ':' + str(src[1]))
            if m.method: # request: update Via and call receivedRequest
                if m.Via == None:
                    raise ValueError('No Via header in request')
                via = m.first('Via')
                if via.viaUri.host != src[0] or via.viaUri.port != src[1]:
                    via['received'], via.viaUri.host = src[0], src[0]
                if 'rport' in via:
                    via['rport'] = src[1]
                    via.viaUri.port = src[1]
                if self.transport.type == 'tcp': # assume rport
                    via['rport'] = src[1]
                    via.viaUri.port = src[1]
                if self.fix_nat and m.method in ('INVITE', 'MESSAGE'):
                    self._fixNatContact(m, src)
                self._receivedRequest(m, uri)
            elif m.response: # response: call receivedResponse
                if self.fix_nat and m['CSeq'] and m.CSeq.method in ('INVITE', 'MESSAGE'):
                    self._fixNatContact(m, src)
                self._receivedResponse(m, uri)
            else:
                raise ValueError('Received invalid message')
        except ValueError:
            print("TODO: send 400 response to non-ACK request")
            if _debug:
                print('Error in received message:')
            if _debug: traceback.print_exc()
            if m.method and m.uri and m.protocol and m.method != 'ACK': # this was a non-ACK request
                try: self.send(Message.createResponse(400, str(E), None, None, m))
                except: pass # ignore error since m may be malformed.

    def _fixNatContact(self, m, src):
        if m['Contact']:
            uri = m.first('Contact').value.uri
            if uri.scheme in ('sip', 'sips') and isIPv4(uri.host) and uri.host != src[0] and \
            not isLocal(src[0]) and not isLocal(uri.host) and isPrivate(uri.host) and not isPrivate(src[0]):
                if _debug: print('fixing NAT -- private contact from', uri, end=' ')
                uri.host, uri.port = src[0], src[1]
                if _debug: print('to received', uri)

    def _receivedRequest(self, r, uri):
        '''Received a SIP request r (Message) from the uri (URI).'''
        try: branch = r.first('Via').branch
        except AttributeError: branch = ''
        if r.method == 'ACK':
            if branch == '0':
                # TODO: this is a hack to work around iptel.org which puts branch=0 in all ACK
                # hence it matches the previous transaction's ACK for us, which is not good.
                # We need to fix our code to handle end-to-end ACK correctly in findTransaction.
                t = None
            else:
                t = self.findTransaction(branch) # assume final, non 2xx response
                if not t or t.lastResponse and t.lastResponse.is2xx: # don't deliver to the invite server transaction
                    t = self.findTransaction(Transaction.createId(branch, r.method))
        else:
            t = self.findTransaction(Transaction.createId(branch, r.method))
        if not t: # no transaction found
            app = None  # the application layer for further processing
            if r.method != 'CANCEL' and 'tag' in r.To: # for existing dialog
                d = self.findDialog(r)
                if not d: # no dialog found
                    if r.method != 'ACK':
                        u = self.createServer(r, uri)
                        if u: app = u
                        else:
                            self.send(Message.createResponse(481, 'Dialog does not exist', None, None, r))
                            return
                    else: # hack to locate original t for ACK
                        if _debug: print('no dialog for ACK, finding transaction')
                        if not t and branch != '0': t = self.findTransaction(Transaction.createId(branch, 'INVITE'))
                        if t and t.state != 'terminated':
                            if _debug: print('Found transaction', t)
                            t.receivedRequest(r)
                            return
                        else:
                            if _debug: print('No existing transaction for ACK')
                            u = self.createServer(r, uri)
                            if u: app = u
                            else:
                                if _debug: print('Ignoring ACK without transaction')
                                return
                else: # dialog found
                    app = d
            elif r.method != 'CANCEL': # process all other out-of-dialog request except CANCEL
                u = self.createServer(r, uri)
                if u:
                    app = u
                elif r.method == 'OPTIONS':
                    m = Message.createResponse(200, 'OK', None, None, r)
                    m.Allow = Header('INVITE, ACK, CANCEL, BYE, OPTIONS', 'Allow')
                    self.send(m)
                    return
                elif r.method != 'ACK':
                    self.send(Message.createResponse(405, 'Method not allowed', None, None, r))
                    return
            else: # Process a CANCEL request
                o = self.findTransaction(Transaction.createId(r.first('Via').branch, 'INVITE')) # original transaction
                if not o:
                    self.send(Message.createResponse(481, "Original transaction does not exist", None, None, r))
                    return
                else:
                    app = o.app
            if app:
                t = app.createTransaction(r)
                #t = Transaction.createServer(self, app, r, self.transport, self.tag)
                if r.method == 'ACK' and t is not None and t.id in self.transactions:
                    # Asterisk sends the same branch id in the second call's ACK, and should not match the previous
                    # call's ACK. So we don't add ACK to the transactions list. Another option would be to keep
                    # index in self.transactions as call-id + transaction-id instead of just transaction-id.
                    # In that case there should be a way to remove ACK transactions.
                    del self.transactions[t.id]
            elif r.method != 'ACK':
                self.send(Message.createResponse(404, "Not found", None, None, r))
        else:
            if isinstance(t, ServerTransaction) or isinstance(t, InviteServerTransaction):
                t.receivedRequest(r)
            else:
                # TODO: This is a hack! Need to follow RFC 3261 about creating branch param for proxy
                self.send(Message.createResponse(482, 'Loop detected', None, None, r))


    def _receivedResponse(self, r, uri):
        '''Received a SIP response r (Message) from the uri (URI).'''
        if not r.Via: raise ValueError('No Via header in received response')
        try: branch = r.first('Via').branch
        except AttributeError: branch = ''
        method = r.CSeq.method
        t = self.findTransaction(Transaction.createId(branch, method))
        if not t:
            if method == 'INVITE' and r.is2xx: # success of INVITE
                d = self.findDialog(r)
                if not d: # no dialog or transaction for success response of INVITE.
                    raise ValueError('No transaction or dialog for 2xx of INVITE')
                else:
                    d.receivedResponse(None, r)
            else:
                if _debug: print('transaction id %r not found'%(Transaction.createId(branch, method),)) # do not print the full transactions table
                if method == 'INVITE' and r.isfinal: # final failure response for INVITE, send ACK to same transport
                    # TODO: check if this following is as per the standard
                    m = Message.createRequest('ACK', str(r.To.value.uri))
                    m['Call-ID'], m.From, m.To, m.Via, m.CSeq = r['Call-ID'], r.From, r.To, r.first('Via'), Header(str(r.CSeq.number) + ' ACK', 'CSeq')
                    self.send(m, uri.hostPort)
                raise ValueError('No transaction for response')
        else:
            t.receivedResponse(r)

    # following are the main API methods to indicate events from UAS/UAC/Dialog
    def createServer(self, request, uri): return self.app.createServer(request, uri, self)
    def sending(self, ua, message): return self.app.sending(ua, message, self) if hasattr(self.app, 'sending') else None
    def receivedRequest(self, ua, request): self.app.receivedRequest(ua, request, self)
    def receivedResponse(self, ua, response): self.app.receivedResponse(ua, response, self)
    def cancelled(self, ua, request): self.app.cancelled(ua, request, self)
    def dialogCreated(self, dialog, ua): self.app.dialogCreated(dialog, ua, self)
    def authenticate(self, ua, header): return self.app.authenticate(ua, header, self) if hasattr(self.app, 'authenticate') else False
    def createTimer(self, obj): return self.app.createTimer(obj, self)

    def findDialog(self, arg):
        '''Find an existing dialog for given id (str) or received message (Message).'''
        return self.dialogs.get(isinstance(arg, Message) and Dialog.extractId(arg) or str(arg), None)

    def findTransaction(self, id):
        '''Find an existing transaction for given id (str).'''
        return self.transactions.get(id, None)

    def findOtherTransaction(self, r, orig):
        '''Find another transaction other than orig (Transaction) for this request r (Message).'''
        for t in list(self.transactions.values()):
            if t != orig and Transaction.equals(t, r, orig): return t
        return None

class TransportInfo:
    '''Transport information needed by Stack constructor'''
    def __init__(self, sock, secure=False):
        '''The sock argument is the bound socket.'''
        addr = getlocaladdr(sock)
        self.host, self.port, self.type, self.secure, self.reliable, self.congestionControlled = addr[0], addr[1], (sock.type==socket.SOCK_DGRAM and 'udp' or 'tcp'), secure, (sock.type==socket.SOCK_STREAM), (sock.type==socket.SOCK_STREAM)