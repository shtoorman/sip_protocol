from stack import Stack
from transportinfo import TransportInfo
from header import Header

stack = Stack(self, TransportInfo(sock))
...
stack.received(dataStr, (remoteHost, remotePort))
...
c = Header(str(stack.uri), "Contact")
c.value.uri.user = "shtoorman"
