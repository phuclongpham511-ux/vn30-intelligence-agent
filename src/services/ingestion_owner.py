"""One local collector owner; existing source leases/cooldowns remain authoritative."""
from contextlib import contextmanager
from functools import wraps
import os
from pathlib import Path
from threading import Lock, local
from weakref import WeakKeyDictionary

from sqlalchemy import text
from sqlmodel import Session

_local = local()
_memory_locks = WeakKeyDictionary()
_memory_guard = Lock()
_POSTGRES_LOCK_ID = 87040710767180786


def _key(engine):
    if engine.dialect.name == 'sqlite':
        database = engine.url.database
        if not database or database == ':memory:':
            return ('memory', engine)
        if database.startswith('file:'):
            raise ValueError('Collector ownership requires a regular SQLite database path')
        return ('sqlite', os.path.normcase(str(Path(database).resolve())))
    if engine.dialect.name == 'postgresql':
        return ('postgresql', engine.url)
    raise ValueError('Collector ownership is unsupported for this database')


@contextmanager
def _database_lock(engine, key):
    if key[0] == 'memory':
        with _memory_guard:
            lock = _memory_locks.setdefault(engine, Lock())
        owned = lock.acquire(blocking=False)
        try:
            yield owned
        finally:
            if owned:
                lock.release()
    elif key[0] == 'postgresql':
        # Session-scoped advisory lock: same DB, including independent hosts.
        with engine.connect() as connection:
            owned = connection.execute(text('SELECT pg_try_advisory_lock(:key)'),
                {'key': _POSTGRES_LOCK_ID}).scalar_one()
            try:
                yield owned
            finally:
                if owned:
                    connection.execute(text('SELECT pg_advisory_unlock(:key)'), {'key': _POSTGRES_LOCK_ID})
    else:
        # Local SQLite file mutex survives long crawls without an expiring TTL.
        # Kernel releases ownership on process death; never unlink a lock file.
        with Path(key[1] + '.ingestion.lock').open('a+b') as handle:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b'\0'); handle.flush()
            handle.seek(0)
            owned = False
            try:
                if os.name == 'nt':
                    import msvcrt
                    try:
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                        owned = True
                    except OSError as exc:
                        if exc.errno not in (13, 11):
                            raise
                else:
                    import fcntl
                    try:
                        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        owned = True
                    except BlockingIOError:
                        pass
                yield owned
            finally:
                if owned:
                    handle.seek(0)
                    if os.name == 'nt':
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(handle, fcntl.LOCK_UN)


@contextmanager
def collector_owner(engine):
    """Reentrant on the owning thread, exclusive across processes and other threads."""
    engine = engine.engine  # normalize Session binds that are Connection objects
    key = _key(engine)
    owners = getattr(_local, 'owners', set())
    if key in owners:
        yield True
        return
    with _database_lock(engine, key) as owned:
        if owned:
            _local.owners = owners | {key}
        try:
            yield owned
        finally:
            if owned:
                _local.owners = owners


def collector_owned(function):
    """Guard existing Session/Engine public cycle seams, including manual callers."""
    @wraps(function)
    def guarded(*args, **kwargs):
        resource = args[0] if args else kwargs.get('session', kwargs.get('engine'))
        engine = resource.get_bind() if isinstance(resource, Session) else resource
        with collector_owner(engine) as owned:
            if not owned:
                return {'status': 'collector_busy'}
            return function(*args, **kwargs)
    return guarded
