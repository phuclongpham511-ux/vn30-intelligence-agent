"""Run the approved synthetic-only LLM gateway on HTTPS loopback only."""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import ssl
import sys
from urllib.parse import urlsplit

from src.schemas.financial_evaluation import LiveEvaluationConfig
from src.services.financial_model_adapter import EvaluationStopped
from src.services.financial_llm_gateway import GatewayProcessLock, RealLLMGateway

BIND_HOST = '127.0.0.1'


def configured_port(endpoint_url):
    endpoint = urlsplit(endpoint_url)
    if endpoint.hostname not in ('localhost', BIND_HOST) or endpoint.path != '/evaluate':
        raise ValueError('gateway_endpoint_must_be_loopback')
    return endpoint.port or 443


class LocalGatewayServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False


def run(*, on_ready=None):
    process_lock = server = None
    try:
        config_path = Path(os.environ['WOOFI_LLM_GATEWAY_CONFIG'])
        state_path = os.environ['WOOFI_LLM_GATEWAY_STATE']
        process_lock = GatewayProcessLock(state_path)
        cert_path = os.environ['WOOFI_LLM_GATEWAY_TLS_CERT']
        key_path = os.environ['WOOFI_LLM_GATEWAY_TLS_KEY']
        config = LiveEvaluationConfig.model_validate_json(config_path.read_bytes())
        token = os.environ.get('WOOFI_LLM_GATEWAY_TOKEN', '')
        gateway = RealLLMGateway(config, token, state_path)
        port = configured_port(config.endpoint)
        class Handler(BaseHTTPRequestHandler):
            server_version = 'WoofiGateway/1'
            sys_version = ''

            def log_message(self, fmt, *args):
                # Never log body, token, provider response or exception details.
                sys.stderr.write('woofi-gateway request\n')

            def do_POST(self):
                if self.path != '/evaluate' or self.headers.get('Transfer-Encoding'):
                    return self.reply(404)
                try:
                    if (self.headers.get_content_type() != 'application/json' or
                            len(self.headers.get_all('Content-Length', [])) != 1 or
                            len(self.headers.get_all('Authorization', [])) != 1 or
                            len(self.headers.get_all('X-Woofi-Run-ID', [])) != 1):
                        return self.reply(400)
                    length = int(self.headers.get('Content-Length', '-1'))
                    if length < 1 or length > 65536:
                        return self.reply(413)
                    body = self.rfile.read(length)
                    result = gateway.handle(body, self.headers.get('Authorization'),
                        self.headers.get('X-Woofi-Run-ID'))
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Cache-Control', 'no-store')
                    self.send_header('Content-Length', str(len(result)))
                    self.end_headers()
                    self.wfile.write(result)
                except EvaluationStopped as error:
                    status = 401 if 'unauthorized' in str(error) else 403
                    self.reply(status)
                except Exception:
                    self.reply(502)

            def reply(self, status):
                body = b'{"error":"gateway_request_rejected"}'
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self): self.reply(405)
            def do_PUT(self): self.reply(405)
            def do_DELETE(self): self.reply(405)

        server = LocalGatewayServer((BIND_HOST, port), Handler)
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
        tls.load_cert_chain(certfile=cert_path, keyfile=key_path)
        server.socket = tls.wrap_socket(server.socket, server_side=True)
        if on_ready is not None:
            on_ready(server)
        print('Woofi synthetic LLM gateway listening on HTTPS loopback; Ctrl+C to stop.', file=sys.stderr)
        server.serve_forever()
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception:
        print('Gateway startup refused; verify approved config, loopback TLS and secret environment.', file=sys.stderr)
        return 2
    finally:
        if server is not None:
            server.server_close()
        if process_lock is not None:
            process_lock.close()


if __name__ == '__main__':
    raise SystemExit(run())
