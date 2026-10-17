const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { randomUUID } = require('node:crypto');
const { BASE_URL, launch, login, testCredentials, api } = require('./helpers.cjs');

(async () => {
  assert(process.env.TEST_BACKEND_CONTAINER, 'Use the disposable browser runner.');
  const shell = code => execFileSync('docker', ['exec', '-i', process.env.TEST_BACKEND_CONTAINER,
    'python', 'manage.py', 'shell'], { input: code, encoding: 'utf8' }).trim().split('\n').at(-1);
  const tag = randomUUID();
  const data = JSON.parse(shell(`
import base64, io, json
from pathlib import Path
from PIL import Image
from django.conf import settings
from django.db.models import Q
from demo.data import demo_id
from apps.matches.models import Match
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantPhoto, EventOutfitPhoto
from apps.reports.models import Report, ReportEvidence
actor = EventParticipant.objects.get(pk=demo_id('actor'))
peer = EventParticipant.objects.get(event=actor.event, profile__first_name='Mariana')
output = io.BytesIO()
Image.new('RGB', (2, 2), 'blue').save(output, format='PNG')
content = output.getvalue()
prefix = 'media-check/${tag}/'
def store(name):
    key = prefix + name
    path = Path(settings.MEDIA_ROOT, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return key
own = ParticipantPhoto.objects.create(participant=actor, storage_key=store('own.png'))
public = ParticipantPhoto.objects.create(participant=peer, storage_key=store('public.png'))
private = ParticipantPhoto.objects.create(participant=peer, storage_key=store('private.png'), visibility='POST_MATCH')
escaped = ParticipantPhoto.objects.create(participant=actor, storage_key=store('olá 100% #?.png'))
literal = ParticipantPhoto.objects.create(participant=actor, storage_key=store('%2e%2e/literal.png'))
previous_outfit_key = EventOutfitPhoto.objects.filter(participant=peer).values_list('storage_key', flat=True).first()
outfit, _ = EventOutfitPhoto.objects.update_or_create(participant=peer, defaults={'storage_key':store('outfit.png')})
report = Report.objects.create(reporter=actor, reported=peer, reason='Media test')
evidence = ReportEvidence.objects.create(report=report, storage_key=store('evidence.png'))
match = Match.objects.get(Q(participant=actor, partner=peer) | Q(participant=peer, partner=actor))
def url(route): return '/api/events/' + str(actor.event_id) + '/' + route
print(json.dumps({'own':url('photos/'+str(own.pk)+'/content/'), 'public':url('photos/'+str(public.pk)+'/content/'),
    'private':url('photos/'+str(private.pk)+'/content/'), 'escaped':url('photos/'+str(escaped.pk)+'/content/'),
    'literal':url('photos/'+str(literal.pk)+'/content/'), 'outfit':url('outfits/'+str(peer.pk)+'/content/'),
    'admin':url('event-admin/photos/'+str(public.pk)+'/content/'), 'evidence':url('event-admin/evidence/'+str(evidence.pk)+'/content/'),
    'internal':'/_protected_media/'+own.storage_key, 'publicMedia':'/media/'+own.storage_key,
    'key':own.storage_key, 'content':base64.b64encode(content).decode(), 'match':str(match.pk),
    'matchActive':match.is_active, 'photoIds':[str(photo.pk) for photo in [own, public, private, escaped, literal]],
    'outfitId':str(outfit.pk), 'previousOutfitKey':previous_outfit_key, 'reportId':str(report.pk), 'evidenceId':str(evidence.pk)}))
`));
  const expected = Buffer.from(data.content, 'base64');
  const browser = await launch();
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await login(page, testCredentials().email);
    const get = (path, options) => page.request.get(BASE_URL + path, options);
    const nginx = 'http://localhost:18080';
    // Direct calls to the upstream prove it only authorizes and returns headers.
    const upstream = await page.request.get('http://localhost:18000' + data.own);
    assert.equal(upstream.status(), 200);
    assert.equal((await upstream.body()).length, 0);
    assert.equal(upstream.headers()['x-accel-redirect'], data.internal);
    for (const path of [data.own, data.public, data.private, data.escaped, data.literal, data.outfit]) {
      const response = await get(path);
      assert.equal(response.status(), 200, path);
      assert.deepEqual(await response.body(), expected, path);
      assert.equal(response.headers()['content-type'], 'image/png');
      assert.equal(response.headers()['cache-control'], 'private, no-store');
      assert.equal(response.headers()['x-content-type-options'], 'nosniff');
      assert.equal(response.headers()['x-accel-redirect'], undefined, 'Internal redirect header must not reach the browser');
    }
    const head = await page.request.head(BASE_URL + data.own);
    assert.equal(head.status(), 200);
    assert.equal(Number(head.headers()['content-length']), expected.length);
    assert.equal((await head.body()).length, 0);
    const range = await get(data.own, { headers: { Range: 'bytes=0-7' } });
    assert.equal(range.status(), 206);
    assert.deepEqual(await range.body(), expected.subarray(0, 8));
    assert.equal(range.headers()['content-range'], `bytes 0-7/${expected.length}`);
    for (const path of [data.internal, data.publicMedia]) {
      assert.equal((await page.request.get(nginx + path)).status(), 404, 'Raw media paths must remain private');
    }
    const anonymous = await browser.newContext();
    const denied = await anonymous.request.get(nginx + data.own);
    assert.equal(denied.status(), 401);
    assert.notDeepEqual(await denied.body(), expected);
    await anonymous.close();
    shell(`from apps.matches.models import Match; Match.objects.filter(pk='${data.match}').update(is_active=False)`);
    for (const path of [data.private, data.outfit]) {
      const response = await get(path);
      assert.equal(response.status(), 403);
      assert.equal(response.headers()['x-accel-redirect'], undefined);
    }
    shell(`from apps.matches.models import Match; Match.objects.filter(pk='${data.match}').update(is_active=True)`);
    // Render a real protected image in the browser, in addition to checking bytes.
    await page.evaluate(src => { const image = document.createElement('img'); image.id = 'media-probe'; image.src = src; document.body.append(image); }, data.own);
    await page.waitForFunction(() => document.getElementById('media-probe')?.naturalWidth === 2);
    const admin = await browser.newPage();
    await login(admin, testCredentials().adminEmail);
    const photo = await admin.request.get(BASE_URL + data.admin);
    assert.deepEqual(await photo.body(), expected);
    const evidence = await admin.request.get(BASE_URL + data.evidence);
    assert.equal(evidence.status(), 200);
    assert.deepEqual(await evidence.body(), expected);
    assert(evidence.headers()['content-disposition'].startsWith('attachment;'));
    assert.equal(shell(`from apps.audit.models import AuditLog; print(AuditLog.objects.filter(action='evidence.viewed', object_id='${data.evidence.split('/').at(-3)}').exists())`), 'True');
    await api(page, 'auth/logout/', 'POST');
    assert.equal((await get(data.own)).status(), 401);
    assert.deepEqual(errors, []);
    console.log('PASS: Django authorizes without bytes; Nginx delivers exact private image/evidence bytes, Unicode and literal escapes, HEAD/Range, internal-path denial, match checks, audit and logout.');
  } finally {
    try {
      // This scenario shares the seeded actor with subsequent profile tests.
      // Restore only its own fixtures so the actor still has three public photos.
      shell(`
import json
from django.db import connection, transaction
from apps.matches.models import Match
from apps.profiles.models import ParticipantPhoto, EventOutfitPhoto
from apps.reports.models import Report, ReportEvidence
data = json.loads(${JSON.stringify(JSON.stringify(data))})
assert connection.settings_dict['NAME'].startswith('test_browser_')
with transaction.atomic():
    Match.objects.filter(pk=data['match']).update(is_active=data['matchActive'])
    ParticipantPhoto.objects.filter(pk__in=data['photoIds']).delete()
    if data['previousOutfitKey'] is None:
        EventOutfitPhoto.objects.filter(pk=data['outfitId']).delete()
    else:
        EventOutfitPhoto.objects.filter(pk=data['outfitId']).update(storage_key=data['previousOutfitKey'])
    ReportEvidence.objects.filter(pk=data['evidenceId']).delete()
    Report.objects.filter(pk=data['reportId']).delete()
`);
    } finally {
      await browser.close();
    }
  }
})().catch(error => { console.error(error); process.exit(1); });
