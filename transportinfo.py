import socket


class TransportInfo:
    def __init__(self, sock, secure=False):
        addr = getlocaladdr(sock)
        self.host, self.port = addr[0], addr[1]
        self.type = (sock.type==socket.SOCK_DGRAM and ‘udp’ or ‘tcp’)
        self.secure = secure
        self.reliable = self.congestionControlled = (sock.type==socket.SOCK_STREAM)
