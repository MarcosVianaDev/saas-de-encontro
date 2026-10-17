// Bounded probes against the disposable localhost production stack only.
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { launch, testCredentials } = require('../browser/helpers.cjs');
const base = process.env.TEST_PRODUCTION_URL;
const container = process.env.TEST_BACKEND_CONTAINER;
const payload = '</script><img src=x onerror="window.__audit_xss=1">';
const observe = (id, data) => console.log('SECURITY_OBSERVATION ' + JSON.stringify({ id, ...data }));

(async () => {
  assert.equal(new URL(base).hostname, 'localhost');
  const name = execFileSync('docker', ['inspect', '--format', '{{.Name}}', container], { encoding: 'utf8' }).trim();
  assert(name.startsWith('/test-environments-'), 'Only disposable test containers may receive audit fixtures.');
  execFileSync('docker', ['exec', '-i', container, 'python', 'manage.py', 'shell'], {
    encoding: 'utf8', input: `from apps.events.models import Event\nEvent.objects.filter(name='Production check event').update(name=${JSON.stringify(payload)})\n`,
  });
  const browser = await launch();
  try {
    const context = await browser.newContext({ ignoreHTTPSErrors: true });
    const page = await context.newPage();
    const pageErrors = [];
    page.on('pageerror', error => pageErrors.push(error.message));
    await page.route('**/*', route => new URL(route.request().url()).hostname === 'localhost' ? route.continue() : route.abort());
    const login = await page.goto(base);
    observe('PUBLIC_SECURITY_HEADERS', {
      csp: login.headers()['content-security-policy'] || null,
      frameOptions: login.headers()['x-frame-options'] || null,
      hsts: login.headers()['strict-transport-security'] || null,
      nosniff: login.headers()['x-content-type-options'] || null,
    });
    await page.getByLabel('E-mail', { exact: true }).fill(testCredentials().adminEmail);
    await page.getByLabel('Senha', { exact: true }).fill(testCredentials().password);
    await page.getByRole('button', { name: 'Entrar', exact: true }).click();
    await page.locator('.global-administration').waitFor();
    const global = await context.request.get(base + '/spa/global/');
    observe('GLOBAL_SECURITY_HEADERS', {
      csp: global.headers()['content-security-policy'] || null,
      frameOptions: global.headers()['x-frame-options'] || null,
      hsts: global.headers()['strict-transport-security'] || null,
      cache: global.headers()['cache-control'],
    });
    await page.locator('.adm-bottom').getByRole('button', { name: 'Eventos', exact: true }).click();
    await page.getByText(payload, { exact: true }).waitFor();
    assert.equal(await page.evaluate(() => window.__audit_xss), undefined);
    assert.equal(await page.locator('img[onerror]').count(), 0);
    observe('STORED_XSS_EVENT_NAME', { literalVisible: true, executed: false });

    // Another HTTPS port is a different origin but the same site. This models
    // an attacker-controlled sibling origin without contacting any real site.
    const parent = 'https://localhost:9443/audit-parent';
    await page.route(parent, route => route.fulfill({ contentType: 'text/html',
      body: `<iframe src="${base}/spa/global/" style="width:1200px;height:900px"></iframe>` }));
    await page.goto(parent);
    let embedded = false;
    try {
      await page.frameLocator('iframe').locator('.global-administration').waitFor({ timeout: 7000 });
      embedded = true;
    } catch { /* CSP/frame restrictions are the desired outcome after a fix. */ }
    const frameStates = [];
    for (const frame of page.frames().slice(1)) {
      frameStates.push({ url: frame.url(), body: await frame.locator('body').innerText().then(text => text.slice(0, 160)).catch(() => 'unavailable') });
    }
    const frameLoadError = frameStates.some(frame => frame.url.startsWith('chrome-error:'));
    observe('AUTHENTICATED_CROSS_ORIGIN_IFRAME', { embedded, sameSite: true, crossOrigin: true,
      result: embedded ? 'confirmed' : frameLoadError ? 'inconclusive_browser_load_error' : 'not_reproduced',
      frameStates, pageErrors });

    const anonymous = await browser.newContext({ ignoreHTTPSErrors: true });
    const adminLogin = await browser.newContext({ ignoreHTTPSErrors: true });
    const adminToken = await (await adminLogin.request.get(base + '/api/session/')).json();
    const signedIn = await adminLogin.request.post(base + '/mcx/login/', {
      maxRedirects: 0,
      headers: { 'X-CSRFToken': adminToken.csrfToken, Origin: base },
      form: { username: testCredentials().adminEmail, password: testCredentials().password },
    });
    assert.equal(signedIn.status(), 302);
    assert.equal(signedIn.headers().location, '/mcx/');
    assert.equal((await adminLogin.request.get(base + '/mcx/')).status(), 200);
    await adminLogin.close();
    const session = await (await anonymous.request.get(base + '/api/session/')).json();
    const statuses = [];
    for (let attempt = 0; attempt < 12; attempt++) {
      const response = await anonymous.request.post(base + '/mcx/login/', {
        headers: { 'X-CSRFToken': session.csrfToken, Origin: base },
        form: { username: 'nonexistent-audit@example.invalid', password: 'Incorrect-audit-password' },
      });
      statuses.push(response.status());
    }
    observe('PRODUCTION_ADMIN_LOGIN_THROTTLE', { attempts: statuses.length, statuses, limited: statuses.some(status => status === 403 || status === 429) });
    assert(statuses.includes(429), 'Administrative login attempts must be throttled in production.');
    await anonymous.close();
    console.log('PASS: bounded production header, stored XSS, iframe and admin-login probes completed. Observations are findings, not assertions that the project is vulnerability-free.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
