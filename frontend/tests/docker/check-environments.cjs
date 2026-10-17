const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { launch, testCredentials } = require('../browser/helpers.cjs');

(async () => {
  const base = process.env.TEST_PRODUCTION_URL;
  const dev = process.env.TEST_DEVELOPMENT_URL;
  assert(base && dev && process.env.TEST_BACKEND_CONTAINER);
  const browser = await launch();
  try {
    const context = await browser.newContext({ ignoreHTTPSErrors: true });
    const page = await context.newPage();
    const errors = [], requests = [], frames = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => requests.push(new URL(request.url()).pathname));
    page.on('websocket', socket => socket.on('framereceived', frame => frames.push({ url: socket.url(), body: String(frame.payload) })));
    const redirect = await context.request.get(process.env.TEST_PRODUCTION_HTTP_URL, { maxRedirects: 0 });
    assert([301, 308].includes(redirect.status()));
    assert(redirect.headers().location.startsWith('https://'));
    const response = await page.goto(base, { waitUntil: 'networkidle' });
    const html = await response.text();
    assert(!html.includes('/@vite/client') && !html.includes('/main.tsx'));
    const script = page.locator('script[src^="/assets/"]').first();
    const asset = await script.getAttribute('src');
    const compiled = await context.request.get(base + asset);
    assert.equal(compiled.status(), 200);
    assert(compiled.headers()['cache-control'].includes('immutable'));
    const missing = await context.request.get(base + '/assets/not-a-real-chunk.js');
    assert.equal(missing.status(), 404);
    const index = await context.request.get(base + '/index.html');
    assert(index.headers()['cache-control'].includes('no-cache'));
    assert.equal((await context.request.get(base + '/images/profile-placeholder.svg')).status(), 200);
    await page.getByLabel('E-mail', { exact: true }).fill(testCredentials().adminEmail);
    await page.getByLabel('Senha', { exact: true }).fill(testCredentials().password);
    await page.getByRole('button', { name: 'Entrar', exact: true }).click();
    await page.locator('.global-administration').waitFor();
    const deadline = Date.now() + 10000;
    while (Date.now() < deadline && !frames.some(frame => frame.url.startsWith('wss:') && frame.body.includes('ready'))) {
      await page.waitForTimeout(100);
    }
    assert(frames.some(frame => frame.url.startsWith('wss:') && frame.body.includes('ready')), 'Authenticated WSS must connect through production proxies.');
    const title = 'Production WebSocket ' + Date.now();
    execFileSync('docker', ['exec', '-i', process.env.TEST_BACKEND_CONTAINER, 'python', 'manage.py', 'shell'], {
      encoding: 'utf8', input: `from django.contrib.auth import get_user_model\nfrom apps.notifications.models import Notification\nNotification.objects.create(recipient=get_user_model().objects.get(email='admin@example.invalid'), title=${JSON.stringify(title)})\n`,
    });
    await page.getByText(title, { exact: true }).waitFor({ timeout: 6000 });
    const cookies = await context.cookies();
    for (const name of ['sessionid', 'csrftoken']) assert(cookies.find(cookie => cookie.name === name)?.secure, name);
    const admin = await page.goto(base + '/admin/login/');
    assert.equal(admin.status(), 200);
    const css = await context.request.get(base + '/static/admin/css/base.css');
    assert.equal(css.status(), 200);
    assert(css.headers()['content-type'].startsWith('text/css'));
    await page.goto(base + '/#global-dashboard');
    await page.locator('.global-administration').waitFor();
    const popup = context.waitForEvent('page');
    await page.getByRole('button', { name: 'Demonstração', exact: true }).click();
    const demo = await popup;
    await demo.getByLabel('E-mail', { exact: true }).waitFor();
    assert(await demo.getByLabel('Senha', { exact: true }).inputValue());
    assert(!requests.some(path => path === '/@vite/client' || path.endsWith('.tsx')));
    assert.deepEqual(errors, []);

    const development = await browser.newPage();
    development.on('pageerror', error => errors.push(error.message));
    const updates = [];
    development.on('websocket', socket => socket.on('framereceived', frame => updates.push(String(frame.payload))));
    let loaded = false;
    for (let attempt = 0; attempt < 30 && !loaded; attempt++) {
      try { await development.goto(dev + '/#participantes'); loaded = true; }
      catch { await development.waitForTimeout(250); }
    }
    await development.locator('.participant-tile').first().waitFor();
    assert.equal(await development.locator('.participant-tile').count(), 50);
    assert((await (await development.request.get(dev)).text()).includes('/@vite/client'));
    execFileSync('docker', ['exec', process.env.TEST_DEVELOPMENT_CONTAINER, 'node', '-e',
      "require('node:fs').appendFileSync('/app/main.tsx', '\\n// Disposable HMR check\\n')"]);
    const hmrDeadline = Date.now() + 10000;
    while (Date.now() < hmrDeadline && !updates.some(update => update.includes('full-reload') || update.includes('update'))) {
      await development.waitForTimeout(100);
    }
    assert(updates.some(update => update.includes('full-reload') || update.includes('update')), 'Dev image must deliver an HMR update.');
    await development.locator('.participant-tile').first().waitFor();
    assert.deepEqual(errors, []);
    console.log('PASS: compiled assets/cache/404/images, production login/Secure cookies, Admin CSS, WSS push, demo and dev HMR.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
