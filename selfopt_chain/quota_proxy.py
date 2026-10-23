"""Only network exit of the Hermes sandbox: an accounted Unix-socket gateway."""
import json
import secrets
import time
import socketserver
import tempfile
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from selfopt_chain.quota import QuotaExceeded


class QuotaProxy:
    def __init__(self, adapter, ledger, model_id, should_stop):
        self.adapter, self.ledger, self.model_id = adapter, ledger, model_id
        self.should_stop = should_stop
        self.token = secrets.token_hex(24)
        self.usage = {}
        self.events = []
        self.lock = threading.Lock()
        self.directory = tempfile.TemporaryDirectory(prefix='selfopt-proxy-')
        self.path = Path(self.directory.name) / 'gateway.sock'

    def __enter__(self):
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                if self.path != '/v1/chat/completions' or self.headers.get('Authorization') != 'Bearer ' + owner.token:
                    self.send_error(403)
                    return
                try:
                    size = int(self.headers.get('Content-Length', 0))
                    if not 0 < size <= 262144 or owner.should_stop():
                        self.send_error(413)
                        return
                    body = json.loads(self.rfile.read(size))
                    if body.get('model') != owner.model_id or not owner.adapter.policy.actual_allowed(owner.model_id):
                        self.send_error(403)
                        return
                    stream = bool(body.pop('stream', False))
                    body['stream'] = False
                    owner.ledger.record(owner.model_id)
                    started = time.monotonic()
                    with owner.lock:
                        owner.usage[owner.model_id] = owner.usage.get(owner.model_id, 0) + 1
                    request = urllib.request.Request(owner.adapter.base_url + '/chat/completions',
                              data=json.dumps(body).encode(), headers=owner.adapter._headers())
                    with urllib.request.urlopen(request, timeout=owner.adapter.timeout_s) as response:
                        result = json.load(response)
                    if result.get('model') not in {owner.model_id, owner.adapter.policy.response_ids.get(owner.model_id)}:
                        self.send_error(502)
                        return
                    if stream:
                        message = result['choices'][0]['message']
                        chunk = {'id': result.get('id', 'selfopt'), 'object': 'chat.completion.chunk',
                                 'model': owner.model_id, 'choices': [{'index': 0, 'delta': message, 'finish_reason': result['choices'][0].get('finish_reason', 'stop')}]}
                        output = ('data: ' + json.dumps(chunk) + '\n\ndata: [DONE]\n\n').encode()
                        content_type = 'text/event-stream'
                    else:
                        output, content_type = json.dumps(result).encode(), 'application/json'
                    self.send_response(200)
                    self.send_header('Content-Type', content_type)
                    self.send_header('Content-Length', str(len(output)))
                    self.end_headers()
                    try:
                        self.wfile.write(output)
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                    with owner.lock:
                        owner.events.append({'model':owner.model_id,'ok':True,'latency_ms':int((time.monotonic()-started)*1000)})
                    owner.ledger.record_outcome(owner.model_id, {'ok':True,'latency_ms':int((time.monotonic()-started)*1000)})
                except QuotaExceeded:
                    # T60: lokalne wyczerpanie budżetu NIE udaje providera —
                    # jawne oznaczenie origin=local (header + body), by rozróżnić
                    # od realnego 429 upstream (tamten wychodzi z proxy jako 502).
                    payload = json.dumps({'error': {'type': 'local_quota_exhausted',
                                      'origin': 'local', 'message': 'localny limit/budzet roju'}}).encode()
                    self.send_response(429)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('X-Straz-Quota-Origin', 'local')
                    self.send_header('Content-Length', str(len(payload)))
                    self.end_headers()
                    try:
                        self.wfile.write(payload)
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                except (BrokenPipeError, ConnectionResetError):
                    pass
                except Exception as error:
                    with owner.lock:
                        owner.events.append({'model':owner.model_id,'ok':False,'error_class':type(error).__name__})
                    try:
                        self.send_error(502)
                    except (BrokenPipeError, ConnectionResetError):
                        pass
        self.server = socketserver.ThreadingUnixStreamServer(str(self.path), Handler)
        self.server.daemon_threads = True
        self.path.chmod(0o600)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()
