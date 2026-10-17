const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { randomUUID } = require('node:crypto');
const { launch, login, testCredentials } = require('./helpers.cjs');

(async () => {
  assert(process.env.TEST_BACKEND_CONTAINER, 'Use scripts/run-browser-tests.py for disposable fixtures.');
  const shell = code => execFileSync('docker', ['exec', '-i', process.env.TEST_BACKEND_CONTAINER,
    'python', 'manage.py', 'shell'], { input: code, encoding: 'utf8' }).trim().split('\n').at(-1);
  const browser = await launch();
  try {
    const page = await browser.newPage();
    const errors = [];
    let bootstraps = 0, syncs = 0, legacyReads = 0;
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => {
      const path = new URL(request.url()).pathname;
      if (path === '/api/bootstrap/') bootstraps++;
      if (path === '/api/sync/') syncs++;
      if (/\/conversations\/[^/]+\/messages\/$/.test(path) && request.method() === 'GET') legacyReads++;
    });
    await login(page, testCredentials().email);
    await page.evaluate(() => { location.hash = 'mensagens'; });
    await page.locator('.conversation-row').filter({ hasText: 'Mariana' }).click();
    const baseline = bootstraps;
    const text = 'Mensagem incremental ' + randomUUID();
    const fixture = JSON.parse(shell(`
import json
from django.db.models import Q
from demo.data import demo_id
from apps.participants.models import EventParticipant
from apps.matches.models import Match
from apps.messaging.models import Message, Conversation
actor = EventParticipant.objects.get(pk=demo_id('actor'))
peer = EventParticipant.objects.get(event=actor.event, profile__first_name='Mariana')
match = Match.objects.get(Q(participant=actor, partner=peer) | Q(participant=peer, partner=actor))
message = Message.objects.create(conversation=match.conversation, sender=peer, body=${JSON.stringify(text)})
matched = Match.objects.filter(Q(participant=actor) | Q(partner=actor))
known = set(matched.values_list('participant_id', flat=True)) | set(matched.values_list('partner_id', flat=True))
new_peer = EventParticipant.objects.filter(event=actor.event, is_active=True).exclude(pk__in=known | {actor.pk}).first()
first, second = sorted([actor, new_peer], key=lambda person: person.pk.int)
new_match = Match.objects.create(participant=first, partner=second)
Conversation.objects.create(match=new_match)
print(json.dumps({'message':str(message.pk), 'match':str(new_match.pk), 'peer':new_peer.profile.first_name}))
`));
    await Promise.all([
      page.getByText(text, { exact: true }).waitFor({ timeout: 25000 }),
      page.waitForResponse(async response => response.url().includes('/read/')
        && response.status() === 200 && (await response.json()).read.includes(fixture.message), { timeout: 25000 }),
    ]);
    assert.equal(await page.getByText(text, { exact: true }).count(), 1);
    assert.equal(bootstraps, baseline, 'Polling must not request full bootstrap');
    assert.equal(legacyReads, 0, 'Polling must not reload conversation history');
    await page.getByRole('button', { name: 'Voltar às conversas', exact: true }).click();
    await page.locator('.conversation-row').filter({ hasText: fixture.peer }).waitFor();

    // A hidden tab must stay quiet, then synchronize promptly when visible.
    await page.evaluate(() => { Object.defineProperty(document, 'hidden', { configurable: true, value: true }); document.dispatchEvent(new Event('visibilitychange')); });
    const hiddenCount = syncs;
    await page.waitForTimeout(20000);
    assert.equal(syncs, hiddenCount);
    await Promise.all([
      page.waitForResponse(response => new URL(response.url()).pathname === '/api/sync/' && response.status() === 200),
      page.evaluate(() => { Object.defineProperty(document, 'hidden', { configurable: true, value: false }); document.dispatchEvent(new Event('visibilitychange')); }),
    ]);

    const mergeChecks = await page.evaluate(async () => {
      const { mergeMessages, mergePeers } = await import('/participant-sync.ts');
      const original = { id: '1', text: 'First', mine: false, unread: false, created: '2026-01-01T10:00:00Z', updated: '2026-01-01T10:01:00Z' };
      const delta = { chatStates: { peer: { active: true, blocked: false }, empty: { active: true, blocked: false } },
        messages: [{ ...original, peer: 'peer', unread: true, updated: '2026-01-01T10:00:00Z' },
          { id: '2', peer: 'peer', text: 'Second', created: '2026-01-01T10:00:01Z' }], blocked: [], peers: [] };
      const merged = mergeMessages({ peer: [original] }, delta);
      const repeated = mergeMessages(merged, delta);
      const hidden = mergePeers([{id:'hidden',name:'Hidden'}, {id:'peer',name:'Original'}], {
        blocked:['hidden','peer'], chatStates:{peer:{active:false,blocked:true}}, peers:[{id:'peer',name:'Stale catalog name'}, {id:'hidden',name:'Hidden'}],
      });
      return { count: repeated.peer.length, unread: repeated.peer[0].unread, empty: repeated.empty, hidden: hidden.map(person => person.name) };
    });
    assert.deepEqual(mergeChecks, { count: 2, unread: false, empty: [], hidden: ['Usuário bloqueado'] });
    assert.equal(bootstraps, baseline);
    assert.deepEqual(errors, []);
    console.log('PASS: incremental incoming message/read acknowledgement, new empty match, hidden-tab pause/resume, deduplication and no bootstrap/history polling.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
