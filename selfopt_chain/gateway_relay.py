"""Run only inside the network namespace. TCP loopback bridges to one Unix socket."""
import select
import socket
import socketserver
import sys


class Relay(socketserver.BaseRequestHandler):
    def handle(self):
        with socket.socket(socket.AF_UNIX) as remote:
            remote.connect(sys.argv[1])
            sockets = [self.request, remote]
            while True:
                ready, _, _ = select.select(sockets, [], [], 90)
                if not ready:
                    return
                for source in ready:
                    chunk = source.recv(65536)
                    if not chunk:
                        return
                    (remote if source is self.request else self.request).sendall(chunk)


if __name__ == '__main__':
    with socketserver.ThreadingTCPServer(('127.0.0.1', 20129), Relay) as server:
        server.daemon_threads = True
        server.serve_forever()
