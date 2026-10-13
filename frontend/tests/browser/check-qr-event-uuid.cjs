const { BASE_URL, MOCK_URL, launch, testCredentials } = require('./helpers.cjs');
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const eventId = '762d800f-40c3-4f8c-b899-b78523463097';
const differentId = 'faee0fa5-7d37-4a6c-90f1-6b14dbe64f50';
const participant = {
  navigation: 'participant', onboardingComplete: false, active: false,
  profile: {first: '', last: '', month: '1', year: '', gender: 'Prefiro não informar', bio: ''},
  filters: {min: 18, max: 35, gender: 'Todos', interests: [], purpose: 'Networking'},
  people: [], discovery: [], photos: [], chats: {}, chatStates: {}, seen: [], liked: [], saved: [],
  event: {id: eventId, name: 'Evento do QR Code', mode: 'ONLINE', state: 'OPEN'},
};
(async () => {
  const browser = await launch();
  try {
    for (const width of [390, 1440]) {
      const context = await browser.newContext({viewport: {width, height: 900}});
      const page = await context.newPage();
      const errors = [];
      let registerCalls = 0;
      page.on('pageerror', error => errors.push(error.message));
      await page.route('**/api/**', async route => {
        const url = new URL(route.request().url());
        if (url.pathname === '/api/session/') return route.fulfill({json: {authenticated: false, csrfToken: 'qr-test-token', demoEmail: null}});
        if (url.pathname === '/api/bootstrap/') return route.fulfill({json: participant});
        if (url.pathname === '/api/join/test-invite/') {
          if (url.searchParams.get('event') !== eventId) return route.fulfill({status: 400, json: {detail: 'UUID não corresponde ao convite.'}});
          return route.fulfill({json: {id: eventId, name: 'Evento do QR Code'}});
        }
        if (url.pathname === '/api/auth/register/') {
          registerCalls++;
          assert.equal(route.request().method(), 'POST');
          assert.equal(route.request().headers()['x-csrftoken'], 'qr-test-token');
          const data = route.request().postDataJSON();
          assert.equal(data.event, eventId);
          assert.equal(data.invite, 'test-invite');
          return route.fulfill({status: 201, json: {csrfToken: 'new-token', data: participant}});
        }
        throw Error(`Unexpected request ${url.pathname}`);
      });
      for (const path of ['/', `/?event=${eventId}`, `/?event=${differentId}&invite=test-invite`]) {
        await page.goto(`${BASE_URL}${path}`, {waitUntil: 'networkidle'});
        await page.getByLabel('E-mail', {exact: true}).waitFor();
        assert.equal(await page.getByRole('button', {name: /Criar.*conta|Google|Apple/}).count(), 0, `Non-QR options: ${path}`);
      }
      await page.goto(`${BASE_URL}/?event=${eventId}&invite=test-invite`, {waitUntil: 'networkidle'});
      await page.getByRole('button', {name: 'Criar uma conta', exact: true}).waitFor();
      const google = page.getByRole('button', {name: /Continuar com Google/});
      const apple = page.getByRole('button', {name: /Continuar com Apple/});
      await google.waitFor(); await apple.waitFor();
      assert(await google.isDisabled()); assert(await apple.isDisabled());
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await google.scrollIntoViewIfNeeded();
      await page.screenshot({path: `.tools/ui-check/screenshots/qr-login-${width}.png`});
      await page.getByRole('button', {name: 'Criar uma conta', exact: true}).click();
      await page.getByLabel('E-mail', {exact: true}).fill('participant@example.com');
      await page.getByLabel('Senha', {exact: true}).fill('Good-password-2026!');
      await page.getByRole('button', {name: 'Criar conta', exact: true}).click();
      await page.locator('.participant-onboarding').waitFor();
      assert.equal(registerCalls, 1);
      assert.equal(new URL(page.url()).search, '');
      assert.deepEqual(errors, []);
      await context.close();
      console.log(`${width}px: QR options, invalid links, UUID payload and participant onboarding verified.`);
    }
  } finally {await browser.close();}
})().catch(error => {console.error(error); process.exit(1);});
