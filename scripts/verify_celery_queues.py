"""Execute through `manage.py shell` in a Compose backend container.

Uses three real workers, an isolated Redis namespace and temporary task stubs.
Does not create jobs, export files or change application data.
"""
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time

from django.conf import settings
from redis import Redis


def verify():
    tag = secrets.token_hex(6)
    prefix = f'queue-check:{tag}:'
    broker = settings.CELERY_BROKER_URL
    processes = []
    with tempfile.TemporaryDirectory(prefix='queue-check-') as directory:
        root = Path(directory)
        # The real export task runs in the export child, with only its expensive
        # generator replaced by a bounded wait. All routing/retry code is real.
        (root / 'queue_probe.py').write_text('''
import os
import time
from pathlib import Path
import django
django.setup()
from config.celery import app
from apps.events import export_tasks
from apps.passes import tasks as gift_tasks

prefix = os.environ['QUEUE_CHECK_PREFIX']
root = Path(os.environ['QUEUE_CHECK_DIR'])
app.conf.update(
    broker_transport_options={'global_keyprefix': prefix},
    result_backend=app.conf.broker_url,
    result_backend_transport_options={'global_keyprefix': prefix + 'result:'},
)

def blocked_export(identifier):
    assert identifier == 'queue-isolation-probe'
    assert export_tasks.generate.request.delivery_info['routing_key'] == 'exports'
    (root / 'started').write_text('exports', encoding='utf-8')
    deadline = time.monotonic() + 30
    while not (root / 'release').exists():
        if time.monotonic() > deadline:
            raise TimeoutError('Export probe was not released')
        time.sleep(0.05)
    return 'COMPLETED'

export_tasks.generate_export = blocked_export

def blocked_gifts(token, after=None):
    assert token == 'queue-isolation-probe'
    assert gift_tasks.initial_gift_batch.request.delivery_info['routing_key'] == 'gifts'
    (root / 'gifts-started').touch()
    deadline = time.monotonic() + 30
    while not (root / 'release').exists():
        if time.monotonic() > deadline:
            raise TimeoutError('Gift probe was not released')
        time.sleep(0.05)
    return 'GIFTS-COMPLETED'

gift_tasks.initial_gift_batch.run = blocked_gifts
''', encoding='utf-8')
        env = {**os.environ, 'QUEUE_CHECK_PREFIX': prefix, 'QUEUE_CHECK_DIR': str(root),
               'PYTHONPATH': str(root) + os.pathsep + os.environ.get('PYTHONPATH', '')}
        log_files = []
        try:
            # Import the same temporary application in the producer. This changes
            # configuration only inside this disposable verification process.
            os.environ.update(QUEUE_CHECK_PREFIX=prefix, QUEUE_CHECK_DIR=str(root))
            sys.path.insert(0, str(root))
            import queue_probe
            app = queue_probe.app
            nodes = []
            for queue in ('celery', 'exports', 'gifts'):
                name = f'queue-{queue}-{tag}'
                nodes.append(f'{name}@{socket.gethostname()}')
                log = (root / f'{queue}.log').open('w', encoding='utf-8')
                log_files.append(log)
                processes.append(subprocess.Popen([
                    sys.executable, '-m', 'celery', '-A', 'queue_probe', 'worker',
                    '--loglevel=warning', '--concurrency=1', '--pool=prefork',
                    f'--queues={queue}', f'--hostname={name}@%h', '--prefetch-multiplier=1',
                    '--without-gossip', '--without-mingle', '--without-heartbeat',
                ], env=env, stdout=log, stderr=subprocess.STDOUT))
            deadline = time.monotonic() + 25
            while True:
                assert all(process.poll() is None for process in processes), 'A probe worker exited'
                replies = app.control.inspect(destination=nodes, timeout=1).ping() or {}
                if set(replies) == set(nodes):
                    break
                assert time.monotonic() < deadline, 'Probe workers did not start'
            export = queue_probe.export_tasks.generate.delay('queue-isolation-probe')
            gift = queue_probe.gift_tasks.initial_gift_batch.delay('queue-isolation-probe')
            deadline = time.monotonic() + 10
            while not ((root / 'started').exists() and (root / 'gifts-started').exists()):
                assert time.monotonic() < deadline, 'Export/gift did not reach its dedicated worker'
                time.sleep(0.05)
            from config.celery import ping
            assert ping.delay().get(timeout=8) == 'pong', 'Operational queue was blocked'
            assert not export.ready(), 'Export finished before the isolation check'
            assert not gift.ready(), 'Gift batch finished before the isolation check'
            (root / 'release').touch()
            assert export.get(timeout=10) == 'COMPLETED'
            assert gift.get(timeout=10) == 'GIFTS-COMPLETED'
            print('PASS: three real Redis/prefork workers; default task completed while exports and gifts workers were occupied.')
        finally:
            (root / 'release').touch()
            for process in processes:
                process.terminate()
            for process in processes:
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            for log in log_files:
                log.close()
            client = Redis.from_url(broker)
            keys = list(client.scan_iter(match=prefix + '*'))
            if keys:
                client.delete(*keys)


verify()
