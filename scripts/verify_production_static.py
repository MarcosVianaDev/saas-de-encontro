"""Verify collected Django assets through Nginx with DJANGO_DEBUG=0.

Uses a disposable PostgreSQL database, backend, Nginx and static directory.
Requires the Compose db/redis services and existing backend/Nginx images.
"""
import html
import json
from pathlib import Path
import re
import secrets
import subprocess
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]


def run(args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        # Never print resolved Compose configuration or inherited credentials.
        raise RuntimeError(f'Command failed ({result.returncode}): {args[:3]}')
    return result.stdout.strip()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        return None


def fetch(base, path, https=True):
    headers = {'Host': 'static-check.example'}
    if https:
        headers['X-Forwarded-Proto'] = 'https'
    request = urllib.request.Request(base + path, headers=headers)
    opener = urllib.request.build_opener(NoRedirect())
    try:
        response = opener.open(request, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()


def origin(container, port):
    address = run(['docker', 'port', container, str(port) + '/tcp']).splitlines()[0]
    return 'http://' + address


def wait_ready(base):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            if fetch(base, '/api/health/')[0] == 200:
                return
        except (OSError, TimeoutError):
            pass
        time.sleep(0.5)
    raise RuntimeError('Production test backend did not start.')


def main():
    tag = secrets.token_hex(6)
    database = 'test_static_' + tag
    backend = 'saas-static-backend-' + tag
    nginx = 'saas-static-nginx-' + tag
    work = ROOT / '.tools/production-static' / tag
    static = work / 'staticfiles'
    static.mkdir(parents=True)
    created = False
    try:
        command = f'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "CREATE DATABASE {database};"'
        run(['docker', 'compose', 'exec', '-T', 'db', 'sh', '-c', command])
        created = True
        run(['docker', 'compose', 'run', '--no-deps', '-d', '--name', backend,
             '-p', '127.0.0.1::8000', '-e', 'DJANGO_DEBUG=0', '-e', 'DJANGO_SEED_DEMO=0',
             '-e', 'DJANGO_ALLOWED_HOSTS=static-check.example',
             '-e', 'DJANGO_TRUST_PROXY_SSL_HEADER=1', '-e', 'POSTGRES_DB=' + database,
             '-e', 'DJANGO_CACHE_KEY_PREFIX=' + database,
             '-v', f'{static}:/app/staticfiles', 'backend', 'python', 'start.py'])
        upstream = origin(backend, 8000)
        wait_ready(upstream)
        networks = json.loads(run(['docker', 'inspect', '--format', '{{json .NetworkSettings.Networks}}', backend]))
        network, address = next(iter(networks.items()))
        run(['docker', 'run', '-d', '--name', nginx, '--network', network,
             '--add-host', f'backend:{address["IPAddress"]}', '--add-host', 'frontend:127.0.0.1',
             '-p', '127.0.0.1::80', '-v', f'{ROOT / "infra/nginx.conf"}:/etc/nginx/nginx.conf:ro',
             '-v', f'{ROOT / "infra/app-routes.conf"}:/etc/nginx/app-routes.conf:ro',
             '-v', f'{static}:/srv/static:ro', 'nginx:stable-alpine'])
        proxy = origin(nginx, 80)
        wait_ready(proxy)
        assert fetch(upstream, '/static/admin/css/base.css')[0] == 404
        status, headers, _ = fetch(proxy, '/admin/login/', https=False)
        assert status == 301 and headers['Location'].startswith('https://static-check.example/')
        status, _, body = fetch(proxy, '/admin/login/')
        assert status == 200
        assets = set(html.unescape(path) for path in re.findall(r'(?:src|href)="(/static/[^"]+)"', body.decode()))
        assets.add('/static/admin/img/icon-yes.svg')
        assert any(path.endswith('.css') for path in assets)
        assert any(path.endswith('.js') for path in assets)
        for path in sorted(assets):
            status, headers, content = fetch(proxy, path)
            assert status == 200, path
            filename = static / path.removeprefix('/static/').split('?', 1)[0]
            assert content == filename.read_bytes(), path
            assert headers['X-Content-Type-Options'] == 'nosniff'
            mime = headers.get_content_type()
            if path.endswith('.css'):
                assert mime == 'text/css', (path, mime)
            elif path.endswith('.js'):
                assert mime in {'text/javascript', 'application/javascript'}, (path, mime)
            elif path.endswith('.svg'):
                assert mime == 'image/svg+xml', (path, mime)
        assert fetch(proxy, '/static/does-not-exist.css')[0] == 404
        assert fetch(proxy, '/static/')[0] in {403, 404}
        # The Compose backend probe must also stay healthy under production
        # redirects and hosts that do not include localhost.
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            status = run(['docker', 'inspect', '--format', '{{.State.Health.Status}}', backend])
            if status == 'healthy':
                break
            time.sleep(0.5)
        assert status == 'healthy', 'Production backend healthcheck failed.'
        run(['docker', 'exec', nginx, 'wget', '-q', '-O', '/dev/null',
             'http://127.0.0.1/static/admin/css/base.css'])
        print(f'PASS: DEBUG=0; {len(assets)} collected assets, CSS/JS/SVG MIME types, HTTPS redirect, missing files and healthchecks.', flush=True)
        print(f'Isolated static artifacts: {work}', flush=True)
    finally:
        with (work / 'backend.log').open('w', encoding='utf-8') as output:
            subprocess.run(['docker', 'logs', backend], cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
        for container in [nginx, backend]:
            subprocess.run(['docker', 'rm', '-f', container], capture_output=True)
        if created:
            assert re.fullmatch(r'test_static_[a-f0-9]{12}', database)
            command = f'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "DROP DATABASE {database} WITH (FORCE);"'
            run(['docker', 'compose', 'exec', '-T', 'db', 'sh', '-c', command])


if __name__ == '__main__':
    main()
