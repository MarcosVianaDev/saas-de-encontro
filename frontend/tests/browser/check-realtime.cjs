const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { randomUUID } = require('node:crypto');
const { launch, login, testCredentials, selectEvent } = require('./helpers.cjs');

(async () => {
  assert(process.env.TEST_BACKEND_CONTAINER, 'Use the disposable browser runner.');
  const shell = code => execFileSync('docker', ['exec', '-i', process.env.TEST_BACKEND_CONTAINER,
    'python', 'manage.py', 'shell'], { input: code, encoding: 'utf8' });
  const browser = await launch();
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    let blocked = false, connections = 0, syncs = 0, bootstraps = 0;
    let activeRoute;
    await page.routeWebSocket('**/ws/**', route => {
      connections++;
      if (blocked) { void route.close(); return; }
      activeRoute = route;
      route.connectToServer();
    });
    page.on('request', request => {
      const path = new URL(request.url()).pathname;
      if (path === '/api/sync/') syncs++;
      if (path === '/api/bootstrap/') bootstraps++;
    });
    await login(page, testCredentials().email);
    await page.waitForFunction(async () => (await import('/realtime.ts')).realtimeConnected());
    await page.evaluate(() => { location.hash = 'mensagens'; });
    await page.locator('.conversation-row').filter({ hasText: 'Mariana' }).click();
    await page.waitForTimeout(1500);
    const baseline = bootstraps, count = syncs;
    const initialConnections = connections;
    await page.waitForTimeout(19000);
    assert.equal(syncs, count, 'Healthy WebSocket must replace 15-second message polling');
    assert.equal(connections, initialConnections, 'Messages/notifications must share one connection');
    const text = 'WebSocket real ' + randomUUID();
    const notice = 'Aviso real ' + randomUUID();
    const create = (body, title) => shell(`
from django.db import transaction
from django.db.models import Q
from demo.data import demo_id
from apps.participants.models import EventParticipant
from apps.matches.models import Match
from apps.messaging.models import Message
from apps.notifications.models import Notification
actor = EventParticipant.objects.get(pk=demo_id('actor'))
peer = EventParticipant.objects.get(event=actor.event, profile__first_name='Mariana')
match = Match.objects.get(Q(participant=actor, partner=peer) | Q(participant=peer, partner=actor))
with transaction.atomic():
    Message.objects.create(conversation=match.conversation, sender=peer, body=${JSON.stringify(body)})
    Notification.objects.create(participant=actor, event=actor.event, title=${JSON.stringify(title)}, body='Aviso de teste em tempo real')
`);
    create(text, notice);
    await page.getByText(text, { exact: true }).waitFor({ timeout: 4000 });
    await page.locator('.notification-toast-container').getByText(notice, { exact: true }).waitFor({ timeout: 4000 });
    assert.equal(await page.getByText(text, { exact: true }).count(), 1);
    assert.equal(bootstraps, baseline);

    // Force a transport failure and refuse all reconnects. HTTP must recover.
    blocked = true;
    await activeRoute.close();
    await page.waitForFunction(async () => !(await import('/realtime.ts')).realtimeConnected());
    await page.waitForTimeout(1200);
    const fallback = 'Fallback HTTP ' + randomUUID();
    create(fallback, 'Fallback aviso ' + randomUUID());
    await page.getByText(fallback, { exact: true }).waitFor({ timeout: 22000 });
    assert.equal(bootstraps, baseline);
    blocked = false;
    await page.waitForFunction(async () => (await import('/realtime.ts')).realtimeConnected(), null, { timeout: 40000 });
    assert.equal(await page.getByText(fallback, { exact: true }).count(), 1);

    // The same transport is used by the global and event administration access.
    const admin = await browser.newPage();
    await login(admin, testCredentials().adminEmail);
    await admin.waitForFunction(async () => (await import('/realtime.ts')).realtimeConnected());
    const globalNotice = 'Alerta global ' + randomUUID();
    shell(`
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification
Notification.objects.bulk_create([Notification(recipient=get_user_model().objects.get(email=${JSON.stringify(testCredentials().adminEmail)}), title=${JSON.stringify(globalNotice)})])
`);
    await admin.getByText(globalNotice, { exact: true }).waitFor({ timeout: 4000 });
    await selectEvent(admin);
    await admin.waitForFunction(async () => (await import('/realtime.ts')).realtimeConnected());
    assert.deepEqual(errors, []);
    console.log('PASS: authenticated real Redis cross-process WebSocket, one connection per tab, immediate messages/notifications/global alerts, no idle polling, HTTP fallback and reconnect without duplicates.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
