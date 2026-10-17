const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { BASE_URL, launch, testCredentials, login, api } = require('./helpers.cjs');

(async () => {
  assert(process.env.TEST_BACKEND_CONTAINER, 'Run through scripts/run-browser-tests.py to use disposable fixtures.');
  const fixture = `
import json
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.events.models import Event
owner = get_user_model().objects.filter(is_superuser=True).first()
org = Organization.objects.first()
events = [Event.objects.create(organization=org, responsible=owner, name=name, mode='ONLINE') for name in ['Evento da aba A', 'Evento da aba B']]
print(json.dumps([str(event.pk) for event in events]))
`;
  const output = execFileSync('docker', ['exec', '-i', process.env.TEST_BACKEND_CONTAINER,
    'python', 'manage.py', 'shell'], { input: fixture, encoding: 'utf8' });
  const [first, second] = JSON.parse(output.trim().split('\n').at(-1));
  const browser = await launch();
  try {
    const context = await browser.newContext();
    const tabA = await context.newPage();
    await login(tabA, testCredentials().adminEmail);
    await api(tabA, 'global/event/', 'POST', { event: first });
    await tabA.reload({ waitUntil: 'networkidle' });
    await tabA.getByLabel('Nome', { exact: true }).waitFor();
    const tabB = await context.newPage();
    await tabB.goto(BASE_URL, { waitUntil: 'networkidle' });
    await api(tabB, 'event-admin/', 'POST', { event: second });
    await tabB.reload({ waitUntil: 'networkidle' });
    await tabB.getByLabel('Nome', { exact: true }).waitFor();

    const changes = [];
    tabA.on('request', request => {
      if (request.method() === 'PUT' && request.url().endsWith('/event-admin/configuration/'))
        changes.push(request.headers()['x-event-id']);
    });
    await tabA.getByLabel('Nome', { exact: true }).fill('Evento A atualizado na própria aba');
    await tabA.getByRole('button', { name: 'Salvar alterações', exact: true }).click();
    await tabA.getByText('Configurações atualizadas.', { exact: true }).waitFor();
    assert.deepEqual(changes, [first]);
    assert.equal((await api(tabA, 'event-admin/')).event.name, 'Evento A atualizado na própria aba');
    assert.equal((await api(tabB, 'event-admin/')).event.name, 'Evento da aba B');

    await tabA.reload({ waitUntil: 'networkidle' });
    assert.equal(await tabA.getByLabel('Nome', { exact: true }).inputValue(), 'Evento A atualizado na própria aba');
    await tabB.reload({ waitUntil: 'networkidle' });
    assert.equal(await tabB.getByLabel('Nome', { exact: true }).inputValue(), 'Evento da aba B');
    assert.equal((await tabA.evaluate(() => JSON.parse(sessionStorage.getItem('eventconnect-tab-context')))).eventId, first);
    assert.equal((await tabB.evaluate(() => JSON.parse(sessionStorage.getItem('eventconnect-tab-context')))).eventId, second);
    console.log('PASS: shared session, independent event tabs, scoped UI write and reload persistence.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
