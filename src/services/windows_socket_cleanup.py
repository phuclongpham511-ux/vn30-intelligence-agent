"""Keep Windows peer resets from interrupting asyncio's socket teardown.

CPython's Proactor calls socket.shutdown before close/server._detach. A peer
reset there otherwise leaks the server attachment and hangs wait_closed, before
Uvicorn can run application/SQLite cleanup. Preserve the original teardown and
handle only the already-reset socket's shutdown call; pipes are untouched.
"""
from functools import wraps
import sys


class _ResetSafeShutdown:
    def __init__(self, sock):
        self.sock = sock

    def __getattr__(self, name):
        return getattr(self.sock, name)

    def shutdown(self, how):
        try:
            return self.sock.shutdown(how)
        except ConnectionResetError:
            # Peer has already reset this connection. Still close our handle
            # and let the original callback detach exactly once from its server.
            return None


def _reset_safe_callback(original):
    @wraps(original)
    def connection_lost(transport, exc):
        sock = transport._sock
        if sock is None or transport._called_connection_lost:
            return original(transport, exc)
        proxy = _ResetSafeShutdown(sock)
        transport._sock = proxy
        try:
            return original(transport, exc)
        finally:
            # Unknown errors remain errors, with the original socket retained.
            # On successful cleanup CPython has already set _sock to None.
            if transport._sock is proxy:
                transport._sock = sock
    connection_lost._woofi_reset_safe = True
    return connection_lost


def install_windows_socket_cleanup():
    """Process-local, idempotent Backend bootstrap; never patch stdlib files."""
    if sys.platform != 'win32':
        return False
    from asyncio.proactor_events import _ProactorSocketTransport
    original = _ProactorSocketTransport._call_connection_lost
    if not getattr(original, '_woofi_reset_safe', False):
        _ProactorSocketTransport._call_connection_lost = _reset_safe_callback(original)
    return True
