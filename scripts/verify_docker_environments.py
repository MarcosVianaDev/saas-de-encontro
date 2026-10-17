"""Build and exercise dev/prod images in an isolated Compose project.

Production uses its actual compose/configuration with local TLS and no ACME
network requests. All database, Redis, data, credentials and ports are temporary.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]
IMAGES = {'backend': 'saas-backend-production-check',
          'frontend': 'saas-frontend-production-check',
          'development': 'saas-frontend-development-check'}


def run(args, **kwargs):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', **kwargs)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {args[:4]}\n{result.stderr[-3000:]}')
    return result.stdout.strip()


def origin(container, port, https=False):
    address = run(['docker', 'port', container, str(port) + '/tcp']).splitlines()[0]
    return ('https://' if https else 'http://') + 'localhost:' + address.rsplit(':', 1)[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-build', action='store_true', help='Use images built by a previous verification.')
    options = parser.parse_args()
    tag = secrets.token_hex(6)
    project = 'test-environments-' + tag
    dev_container = project + '-vite'
    work = ROOT / '.tools/docker-environments' / tag
    work.mkdir(parents=True)
    password = 'Fixture!' + secrets.token_hex(16)
    env_file = work / 'production.env'
    credentials = work / 'credentials.json'
    credentials.write_text(json.dumps({'adminEmail': 'admin@example.invalid',
                                      'managerEmail': 'manager@example.invalid',
                                      'participantEmail': 'participant@example.invalid',
                                      'password': password}), encoding='utf-8')
    env_file.write_text('\n'.join([
        'APP_DOMAIN=localhost', 'ACME_EMAIL=fixture@example.invalid', 'APP_VERSION=check',
        'PROD_DATA_DIR=' + str(work / 'data').replace('\\', '/'),
        'DJANGO_SECRET_KEY=' + secrets.token_hex(32), 'POSTGRES_DB=test_environment',
        'POSTGRES_USER=fixture', 'POSTGRES_PASSWORD=' + secrets.token_hex(24),
    ]) + '\n', encoding='utf-8')
    env = {**os.environ, 'PROD_ENV_FILE': str(env_file), 'APP_DOMAIN': 'localhost',
           'ACME_EMAIL': 'fixture@example.invalid', 'PROD_DATA_DIR': str(work / 'data'), 'APP_VERSION': 'check'}
    stack_file = work / 'compose.json'
    compose = ['docker', 'compose', '-p', project, '-f', str(stack_file)]
    try:
        # Explicit dev must preserve the existing project's resources and HMR.
        default = json.loads(run(['docker', 'compose', 'config', '--format', 'json']))
        development = json.loads(run(['docker', 'compose', '-f', 'docker-compose.dev.yml', 'config', '--format', 'json']))
        for key in ['services', 'volumes', 'networks']:
            assert development[key] == default[key], key
        config = json.loads(run(['docker', 'compose', '--env-file', str(env_file), '-p', project,
                                 '-f', 'docker-compose.prod.yml', 'config', '--format', 'json'], env=env))
        frontend = config['services']['frontend']
        assert frontend['build']['target'] == 'production'
        assert frontend['build']['args']['VITE_FRONTEND_DATA_MODE'] == 'django'
        assert not frontend.get('volumes') and not frontend.get('environment')
        for service in ['backend', 'celery_worker', 'celery_exports', 'celery_gifts', 'celery_beat']:
            assert config['services'][service]['environment']['DJANGO_DEBUG'] == '0'
            assert config['services'][service]['environment']['DJANGO_SEED_DEMO'] == '0'
            assert all(m['target'] != '/app' for m in config['services'][service]['volumes'])
        if not options.skip_build:
            builds = [(['-f', 'backend/Dockerfile', '.'], IMAGES['backend']),
                      (['--target', 'production', '--build-arg', 'VITE_FRONTEND_DATA_MODE=django', 'frontend'], IMAGES['frontend']),
                      (['--target', 'development', 'frontend'], IMAGES['development'])]
            for index, (args, image) in enumerate(builds):
                with (work / f'build-{index}.log').open('w', encoding='utf-8') as output:
                    result = subprocess.run(['docker', 'build', '-t', image, *args], cwd=ROOT,
                                            stdout=output, stderr=subprocess.STDOUT)
                if result.returncode:
                    raise RuntimeError(f'Image build failed: {image}. Inspect build-{index}.log')
        for service in ['backend', 'celery_worker', 'celery_exports', 'celery_gifts', 'celery_beat', 'frontend']:
            config['services'][service].pop('build', None)
            config['services'][service]['image'] = IMAGES['frontend' if service == 'frontend' else 'backend']
        for service in config['services'].values():
            service['restart'] = 'no'
        # Use Traefik's local certificate. Never contact Let's Encrypt in tests.
        traefik = config['services']['traefik']
        traefik['command'] = [value for value in traefik['command'] if not value.startswith('--certificatesresolvers.')]
        traefik['ports'] = [{'target': 80, 'host_ip': '127.0.0.1', 'protocol': 'tcp'},
                           {'target': 443, 'host_ip': '127.0.0.1', 'protocol': 'tcp'}]
        routes = work / 'traefik.yml'
        routes.write_text((ROOT / 'infra/traefik.prod.yml').read_text(encoding='utf-8').replace(
            'tls:\n        certResolver: letsencrypt', 'tls: {}'), encoding='utf-8')
        for mount in traefik['volumes']:
            if mount['target'] == '/etc/traefik/routes.yml':
                mount['source'] = str(routes)
        stack_file.write_text(json.dumps(config), encoding='utf-8')
        print('Starting the disposable production stack with local HTTPS.', flush=True)
        run([*compose, 'up', '-d', '--no-build', '--wait', '--wait-timeout', '180'])
        backend = run([*compose, 'ps', '-q', 'backend'])
        gateway = run([*compose, 'ps', '-q', 'traefik'])
        frontend_container = run([*compose, 'ps', '-q', 'frontend'])
        assert run(['docker', 'exec', frontend_container, 'sh', '-c',
                    'test ! -d /app/node_modules && ! command -v node && ! command -v npm']) == ''
        assert 'nginx' in run(['docker', 'top', frontend_container])
        with (work / 'backend-tests.log').open('w', encoding='utf-8') as output:
            # Test clients use HTTP internally; only this test process disables
            # the production HTTPS redirect. Browser checks still exercise TLS.
            result = subprocess.run([*compose, 'exec', '-T', '-e', 'DJANGO_DEBUG=1', 'backend', 'python', 'manage.py', 'test',
                                     'api.test_frontend_delivery', 'api.test_event_scope',
                                     'api.test_event_requests', '--noinput'], cwd=ROOT,
                                    stdout=output, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError('Backend permission tests failed. Inspect backend-tests.log')
        fixture = f"""
from django.conf import settings
from django.contrib.auth import get_user_model
assert settings.DEBUG is False
assert get_user_model().objects.count() == 0
get_user_model().objects.create_superuser(username='admin@example.invalid', email='admin@example.invalid', password={password!r})
from datetime import timedelta
from django.utils import timezone
from apps.organizations.models import Organization
from apps.events.models import Event, EventAdministrator
from api.event_admin import join_event
org = Organization.objects.create(name='Production check')
event = Event.objects.create(organization=org, name='Production check event', mode='ONLINE', state='RUNNING', starts_at=timezone.now()-timedelta(hours=1), ends_at=timezone.now()+timedelta(days=1))
manager = get_user_model().objects.create_user(username='manager@example.invalid', email='manager@example.invalid', password={password!r})
EventAdministrator.objects.create(user=manager, event=event)
person = get_user_model().objects.create_user(username='participant@example.invalid', email='participant@example.invalid', password={password!r})
join_event(person, event)
"""
        run(['docker', 'exec', '-i', backend, 'python', 'manage.py', 'shell'], input=fixture)
        network = next(iter(json.loads(run(['docker', 'inspect', '--format', '{{json .NetworkSettings.Networks}}', backend]))))
        run(['docker', 'run', '-d', '--name', dev_container, '--network', network,
             '-e', 'VITE_FRONTEND_DATA_MODE=mock', '-p', '127.0.0.1::5173', IMAGES['development']])
        browser_env = {**os.environ, 'TEST_PRODUCTION_URL': origin(gateway, 443, https=True),
                       'TEST_PRODUCTION_HTTP_URL': origin(gateway, 80),
                       'TEST_DEVELOPMENT_URL': origin(dev_container, 5173),
                       'TEST_BACKEND_CONTAINER': backend, 'TEST_DEVELOPMENT_CONTAINER': dev_container,
                       'TEST_CREDENTIALS_FILE': str(credentials)}
        with (work / 'browser.log').open('w', encoding='utf-8') as output:
            result = subprocess.run(['node', 'frontend/tests/docker/check-environments.cjs'], cwd=ROOT, env=browser_env,
                                    stdout=output, stderr=subprocess.STDOUT, timeout=120)
        if result.returncode:
            raise RuntimeError('Browser verification failed. Inspect browser.log')
        print('PASS: production Compose, immutable backend, no seed, HTTPS, static React, cookies, WebSocket, demo and development HMR.', flush=True)
        print(f'Verification logs: {work}', flush=True)
    finally:
        subprocess.run(['docker', 'rm', '-f', dev_container], capture_output=True)
        if stack_file.exists():
            with (work / 'stack.log').open('w', encoding='utf-8') as output:
                subprocess.run([*compose, 'logs', '--no-color', '--tail', '120'], cwd=ROOT,
                               stdout=output, stderr=subprocess.STDOUT)
            assert project.startswith('test-environments-')
            run([*compose, 'down', '--volumes', '--remove-orphans'])
        credentials.unlink(missing_ok=True)
        env_file.unlink(missing_ok=True)
        stack_file.unlink(missing_ok=True)  # Resolved test-only environment contains credentials.


if __name__ == '__main__':
    main()
