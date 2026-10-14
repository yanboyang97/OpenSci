"""Bounded MCP transport for an operator-established SSH loopback forward.

This is not HTTP/TLS and must never bind publicly. The server fixes its policy;
the remote client receives no coordinator path, OpenAI key, shell or file tool.
"""
import argparse
import hmac
import json
from pathlib import Path
import socket
import socketserver
import sys
import threading

MAX_FRAME = 256_000


def read_token(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Use a protected regular token file')
    with path.open('rb') as handle:
        raw = handle.read(65)
    if len(raw) != 64 or any(c not in b'0123456789abcdef' for c in raw):
        raise ValueError('Use 32 random bytes encoded as 64 lowercase hex characters')
    if sys.platform != 'win32' and path.stat().st_mode & 0o077:
        raise ValueError('Token file must be accessible only by its owner')
    return raw


class LoopbackServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = False
    request_queue_size = 8

    def __init__(self, port, token, factory):
        self.token, self.factory = token, factory
        self.slots = threading.BoundedSemaphore(8)
        super().__init__(('127.0.0.1', port), Session)

    def verify_request(self, request, address):
        return address[0] == '127.0.0.1'

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()

    def handle_error(self, request, client_address):
        # Never log requests, credentials or raw exception text.
        pass


class Session(socketserver.StreamRequestHandler):
    def handle(self):
        from hub_mcp import serve
        self.request.settimeout(10)
        auth = self.rfile.readline(66)
        if not hmac.compare_digest(auth, self.server.token + b'\n'):
            return
        self.wfile.write(b'OK\n')
        self.wfile.flush()
        self.request.settimeout(300)
        serve(self.server.factory(), self.rfile, self.wfile)


def client(port, token, source, destination):
    with socket.create_connection(('127.0.0.1', port), timeout=10) as sock:
        sock.sendall(token + b'\n')
        incoming = sock.makefile('rb')
        if incoming.readline(4) != b'OK\n':
            raise ValueError('Authentication failed')
        sock.settimeout(300)
        # MCP replies may arrive independently; notifications have no reply.
        errors = []
        def receive():
            try:
                while True:
                    raw = incoming.readline(MAX_FRAME + 1)
                    if not raw:
                        break
                    if len(raw) > MAX_FRAME or not raw.endswith(b'\n'):
                        raise ValueError('Invalid remote frame')
                    destination.write(raw)
                    destination.flush()
            except (ValueError, OSError) as exc:
                errors.append(type(exc).__name__)
        worker = threading.Thread(target=receive, daemon=True)
        worker.start()
        try:
            while True:
                raw = source.readline(MAX_FRAME + 1)
                if not raw:
                    break
                if len(raw) > MAX_FRAME or not raw.endswith(b'\n'):
                    raise ValueError('Invalid local frame')
                sock.sendall(raw)
            sock.shutdown(socket.SHUT_WR)
            worker.join(timeout=15)
            if worker.is_alive() or errors:
                raise ValueError('Connection ended without a complete response; recover the original receipt')
        finally:
            sock.close()
        return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='mode', required=True)
    for name in ('server', 'client'):
        parser = sub.add_parser(name)
        parser.add_argument('--port', type=int, required=True)
        parser.add_argument('--token-file', type=Path, required=True)
        if name == 'server':
            parser.add_argument('--coordinator-root', type=Path, required=True)
            parser.add_argument('--policy', type=Path, required=True)
            parser.add_argument('--ready-file', type=Path, required=True)
    args = p.parse_args()
    try:
        if not 0 <= args.port <= 65535 or (args.mode == 'client' and args.port == 0):
            raise ValueError('Invalid port')
        token = read_token(args.token_file)
        if args.mode == 'client':
            return client(args.port, token, sys.stdin.buffer, sys.stdout.buffer)
        from common import read_json
        from hub import Hub
        from hub_mcp import Server, validate_policy
        from storage_paths import plain_path
        policy = validate_policy(read_json(plain_path(args.policy), limit=64000)[0])
        hub = Hub(plain_path(args.coordinator_root))
        with LoopbackServer(args.port, token, lambda: Server(hub, policy)) as server:
            # Exclusive creation prevents accidental replacement of another listener's marker.
            with args.ready_file.open('x', encoding='utf-8') as marker:
                json.dump({'host':'127.0.0.1','port':server.server_address[1]}, marker)
            try:
                server.serve_forever(poll_interval=0.25)
            finally:
                args.ready_file.unlink(missing_ok=True)
        return 0
    except (ValueError, OSError, TypeError, KeyError):
        print('OpenSci remote connection failed. Check the protected policy, token and SSH forward. Recover the original request receipt before retrying a save.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
