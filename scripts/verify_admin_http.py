import http.cookiejar
import os
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

credentials = json.loads(Path(os.getenv('TEST_ADMIN_CREDENTIALS_FILE', '.tools/admin-credentials.json')).read_text(encoding='utf-8-sig'))
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
origin = os.getenv('TEST_BASE_URL', 'http://localhost:8080')
url = origin + '/admin/login/'
page = client.open(url, timeout=10).read().decode()
token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page).group(1)
body = urllib.parse.urlencode({'username': credentials['username'], 'password': credentials['password'], 'csrfmiddlewaretoken': token, 'next': '/admin/'}).encode()
response = client.open(urllib.request.Request(url, data=body, headers={'Referer': url}), timeout=10)
content = response.read().decode()
assert response.geturl() == origin + '/admin/', 'Falha no login'
domains = ['accounts', 'organizations', 'events', 'rooms', 'participants', 'profiles', 'discovery', 'interactions', 'matches', 'messaging', 'passes', 'payments', 'reports', 'moderation', 'consent', 'retention', 'audit', 'notifications', 'analytics']
for domain in domains:
    assert f'/admin/{domain}/' in content, domain
print('Login HTTP com CSRF validado; os 19 apps aparecem no Admin.')
