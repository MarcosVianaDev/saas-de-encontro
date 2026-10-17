"""Run browser checks against a temporary database, media and backups.

Requires running Compose db/redis services, npm ci in frontend, and Edge on Windows
or `npx playwright install chromium` on other platforms. Never resets the live DB.
"""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def run(args, **kwargs):
    result = subprocess.run(args, cwd=ROOT, **kwargs)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {args[:3]}')
    return result


def wait_http(url, process=None):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if process and process.poll() is not None:
            raise RuntimeError('Frontend exited during startup; inspect server.log')
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except (OSError, TimeoutError):
            pass
        time.sleep(0.5)
    raise RuntimeError(f'Test server did not start: {url}')


def reset_test_cache(container):
    # Delete only this run's keys, never FLUSHDB on the shared Redis service.
    script = """
import re
from django.conf import settings
from django.core.cache import cache
from redis import Redis
config = settings.CACHES['default']
assert re.fullmatch(r'test_browser_[a-f0-9]+', config['KEY_PREFIX'])
client = Redis.from_url(config['LOCATION'])
keys = list(client.scan_iter(match=cache.make_key('*')))
if keys:
    client.delete(*keys)
"""
    run(['docker', 'exec', '-i', container, 'python', 'manage.py', 'shell'],
        input=script, text=True, encoding='utf-8', capture_output=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tests', nargs='*', help='Script names; default: all check*.cjs')
    options = parser.parse_args()
    tests_dir = ROOT / 'frontend/tests/browser'
    tests = [tests_dir / name for name in options.tests] if options.tests else sorted(tests_dir.glob('check*.cjs'))
    for test in tests:
        if test.parent != tests_dir or not re.fullmatch(r'check[-\w]*\.cjs', test.name) or not test.is_file():
            raise ValueError(f'Unknown test: {test.name}')
    tag = secrets.token_hex(6)
    database = 'test_browser_' + tag
    container = 'saas-browser-' + tag
    nginx_container = 'saas-browser-nginx-' + tag
    work = ROOT / '.tools/browser-tests' / tag
    work.mkdir(parents=True)
    (ROOT / '.tools/ui-check/screenshots').mkdir(parents=True, exist_ok=True)
    for name in ('media', 'backups', 'staticfiles'):
        (work / name).mkdir()
    password = 'Fixture!' + secrets.token_hex(16)
    credential_file = work / 'credentials.json'
    credential_file.write_text(json.dumps({'email':'browser-participant@example.invalid','adminEmail':'admin-demo@eventconnect.local','password':password}), encoding='utf-8')
    admin_credential_file = work / 'admin-credentials.json'
    admin_credential_file.write_text(json.dumps({'username':'admin-demo@eventconnect.local','password':password}), encoding='utf-8')
    env_file = work / 'backend.env'
    env_file.write_text(f'POSTGRES_DB={database}\nDJANGO_CACHE_KEY_PREFIX={database}\nDRF_NUM_PROXIES=0\nDJANGO_DEBUG=1\nDJANGO_SEED_DEMO=1\nMEDIA_USE_X_ACCEL_REDIRECT=1\nDEMO_USER_EMAIL=browser-participant@example.invalid\nDEMO_USER_PASSWORD={password}\nDJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:18081,http://127.0.0.1:18081\n', encoding='utf-8')
    database_created = False
    backend_started = False
    frontend = None
    results = []
    server_log = (work / 'server.log').open('w', encoding='utf-8')
    try:
        command = f'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "CREATE DATABASE {database};"'
        run(['docker','compose','exec','-T','db','sh','-c',command], capture_output=True)
        database_created = True
        overrides = [flag for line in env_file.read_text(encoding='utf-8').splitlines() for flag in ('-e', line)]
        run(['docker','compose','run','--no-deps','-d','--name',container,'-p','127.0.0.1:18000:8000',*overrides,'-v',f'{work / "media"}:/app/media','-v',f'{work / "backups"}:/app/backups','-v',f'{work / "staticfiles"}:/app/staticfiles','backend','python','start.py'], capture_output=True)
        backend_started = True
        wait_http('http://127.0.0.1:18000/api/health/')
        # Exercise the production X-Accel/authorization path with isolated media.
        network_info = json.loads(run(['docker', 'inspect', '--format', '{{json .NetworkSettings.Networks}}', container],
                                      capture_output=True, text=True, encoding='utf-8').stdout)
        network, address = next(iter(network_info.items()))
        run(['docker', 'run', '-d', '--name', nginx_container, '--network', network,
             '--add-host', f'backend:{address["IPAddress"]}', '--add-host', 'frontend:127.0.0.1',
             '-p', '127.0.0.1:18080:80', '-v', f'{ROOT / "infra/nginx.conf"}:/etc/nginx/nginx.conf:ro',
             '-v', f'{ROOT / "infra/app-routes.conf"}:/etc/nginx/app-routes.conf:ro',
             '-v', f'{work / "media"}:/srv/private-media:ro',
             '-v', f'{work / "staticfiles"}:/srv/static:ro', 'nginx:stable-alpine'], capture_output=True)
        wait_http('http://127.0.0.1:18080/api/health/')
        # Explicit location fixtures for existing physical-event demo participants.
        fixture = "from apps.events.models import Event; from apps.participants.location import reading; from apps.participants.models import EventParticipant; from demo.data import demo_id; e=Event.objects.get(pk=demo_id('event.current')); Event.objects.filter(pk=e.pk).update(latitude='-23.550000',longitude='-46.630000'); [reading(p, {'latitude':'-23.550000','longitude':'-46.630000'}) for p in EventParticipant.objects.filter(event=e)]; print('Browser fixtures ready')"
        run(['docker','exec','-i',container,'python','manage.py','shell','-c',fixture], capture_output=True)
        frontend = subprocess.Popen(['node','frontend/tests/server.mjs'], cwd=ROOT, stdout=server_log, stderr=subprocess.STDOUT)
        wait_http('http://localhost:18081', frontend)
        wait_http('http://localhost:18082', frontend)
        env = {**os.environ,'TEST_BASE_URL':'http://localhost:18081','TEST_MOCK_URL':'http://localhost:18082','TEST_BACKEND_CONTAINER':container,'TEST_CREDENTIALS_FILE':str(credential_file),'TEST_ADMIN_CREDENTIALS_FILE':str(admin_credential_file)}
        for test in tests:
            reset_test_cache(container)
            started = time.monotonic()
            log_file = work / (test.stem+'.log')
            with log_file.open('w', encoding='utf-8') as output:
                child = subprocess.Popen(['node',str(test)],cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT)
                try:
                    code = child.wait(timeout=150)
                except subprocess.TimeoutExpired:
                    if os.name == 'nt':
                        subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True)
                    else:
                        child.kill()
                    child.wait()
                    code = 124
                    output.write('\nRunner timeout (150 seconds).\n')
            result = {'name':test.name,'exit':code,'seconds':round(time.monotonic()-started,1)}
            results.append(result)
            print(json.dumps(result),flush=True)
            (work / 'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        for name in ('verify_scope_gaps.py', 'verify_mvp_concurrency.py', 'verify_admin_http.py'):
            reset_test_cache(container)
            with (work / (name+'.log')).open('w',encoding='utf-8') as output:
                if name == 'verify_admin_http.py':
                    result = subprocess.run([sys.executable,str(ROOT / 'scripts' / name)],cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT)
                else:
                    result = subprocess.run(['docker','exec','-i',container,'python','manage.py','shell'],input=(ROOT / 'scripts' / name).read_text(encoding='utf-8'),text=True,encoding='utf-8',stdout=output,stderr=subprocess.STDOUT)
            results.append({'name':name,'exit':result.returncode})
            print(json.dumps(results[-1]),flush=True)
            (work / 'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    finally:
        if frontend:
            if os.name == 'nt':
                subprocess.run(['taskkill','/PID',str(frontend.pid),'/T','/F'],capture_output=True)
            else:
                frontend.terminate()
            frontend.wait()
        server_log.close()
        try:
            if backend_started:
                reset_test_cache(container)
        finally:
            subprocess.run(['docker','rm','-f',nginx_container],capture_output=True)
            subprocess.run(['docker','rm','-f',container],capture_output=True)
            if database_created:
                assert re.fullmatch(r'test_browser_[a-f0-9]+',database)
                command = f'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "DROP DATABASE {database} WITH (FORCE);"'
                run(['docker','compose','exec','-T','db','sh','-c',command],capture_output=True)
            env_file.unlink(missing_ok=True)
            credential_file.unlink(missing_ok=True)
            admin_credential_file.unlink(missing_ok=True)
    print(f'{len(results)} checks, {sum(r["exit"]==0 for r in results)} completed successfully. Logs: {work}',flush=True)
    return 1 if any(result['exit'] for result in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
