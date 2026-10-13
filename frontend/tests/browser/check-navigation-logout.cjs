const { BASE_URL, MOCK_URL, launch, testCredentials } = require('./helpers.cjs');
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

const participant = {
  navigation: 'participant', onboardingComplete: true, active: true, activated: true,
  profile: { first: 'Camila', last: 'Souza', month: '6', year: '1998', gender: 'Mulheres', bio: 'Amo musica, viagens e boas conversas. Aqui para conhecer pessoas e criar boas historias!' },
  photos: ['/images/photo-1544005313-94ddf0286df2.jpg'], publicPhotos: [],
  filters: { min: 18, max: 35, gender: 'Todos', interests: [], purpose: 'Networking' },
  people: [], discovery: [], chats: {}, chatStates: {}, seen: [], liked: [], saved: [],
  event: { id: 'event-1', name: 'Evento Conexoes 2026', state: 'RUNNING', mode: 'ONLINE' },
};
const admin = {
  role: 'ADMIN', permissions: [], events: [{ id: 'event-1', name: 'Evento Conexoes 2026', role: 'ADMIN' }],
  event: { id: 'event-1', name: 'Evento Conexoes 2026', description: 'Networking e novas conexoes.', starts: '2026-10-04T18:00:00-03:00', ends: '2026-10-04T23:00:00-03:00', status: 'Em andamento', state: 'RUNNING', joinPath: null, responsible: ['Marcos Viana'] },
  participants: [], cases: [], blockSignals: [], team: [],
  metrics: { participants: 284, active: 173, new: 38, matches: 96, conversations: 71, blocks: 0 },
};
const globalData = {
  staff: true, metrics: { RUNNING: 4, SCHEDULED: 24, PAUSED: 0, critical: 3, clients: 18, pending: 3 },
  clients: [{ id: 'client-1', name: 'ACME Eventos', contact: 'Marcos Silva', email: 'marcos@acme.test', active: true, draft: {} }, { id: 'client-2', name: 'Conexoes Corporate', contact: 'Fernanda Lima', email: 'fernanda@corporate.test', active: false, draft: {} }],
  events: [{ id: 'event-1', name: 'Happy Hour Conexoes', state: 'RUNNING', status: 'Em andamento', organization: 'ACME Eventos' }],
  safety: [], alerts: [], activity: [],
};

(async () => {
  const browser = await launch();
  const errors = [];
  try {
    for (const mode of ['participant', 'event', 'global-event', 'global']) {
      const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(`${mode}: ${error.message}`));
      let loggedIn = true, rejectLogout = false, logoutCalls = 0;
      const sessionData = mode === 'global' ? { navigation: 'global' } : mode === 'participant' ? participant : { navigation: 'administration', role: 'ADMIN' };
      await page.route('**/api/**', async route => {
        const path = new URL(route.request().url()).pathname;
        let body;
        if (path === '/api/session/') body = { authenticated: loggedIn, csrfToken: 'test-token', demoEmail: null };
        else if (path === '/api/bootstrap/') body = sessionData;
        else if (path === '/api/global/') body = globalData;
        else if (path === '/api/event-admin/') body = { ...admin, globalContext: mode === 'global-event' };
        else if (path === '/api/notifications/') body = { items: [], unread: 0 };
        else if (path === '/api/event-admin/support/') body = [];
        else if (path === '/api/event-admin/exports/') body = null;
        else if (path === '/api/conversations/') body = { chats: {}, chatStates: {} };
        else if (path === '/api/contexts/') body = { navigation: 'global' };
        else if (path === '/api/auth/login/') { loggedIn = true; body = { csrfToken: 'new-token', data: sessionData }; }
        else if (path === '/api/auth/logout/') {
          logoutCalls++;
          assert.equal(route.request().method(), 'POST');
          assert.equal(route.request().headers()['x-csrftoken'], 'test-token');
          if (rejectLogout) return route.fulfill({ status: 503, json: { detail: 'Falha temporaria ao sair.' } });
          loggedIn = false;
          body = { csrfToken: 'new-token' };
        } else throw Error(`Unexpected API call: ${path}`);
        await route.fulfill({ json: body });
      });
      await page.goto(BASE_URL + '/#perfil');
      const nav = page.locator(mode === 'participant' ? '.bottom-nav' : '.adm-bottom');
      await nav.waitFor();
      for (const width of [320, 390, 768, 1440]) {
        await page.setViewportSize({ width, height: 844 });
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `overflow: ${mode} ${width}`);
        const bounds = await nav.boundingBox();
        assert(bounds && bounds.y > 600 && bounds.y + bounds.height <= 845, `bottom navigation: ${mode} ${width}`);
        assert.equal(await nav.locator('[aria-current="page"]').count(), 1);
        await page.screenshot({ path: `.tools/ui-check/screenshots/navigation-${mode}-${width}.png` });
      }
      if (mode === 'global') {
        await nav.getByRole('button', {name: 'Clientes', exact: true}).click();
        await page.getByRole('button', {name: 'Inativos', exact: true}).click();
        assert.equal(await page.getByRole('heading', {name: 'ACME Eventos', exact: true}).count(), 0);
        await page.getByRole('heading', {name: 'Conexoes Corporate', exact: true}).waitFor();
        await page.getByRole('button', {name: 'Todos', exact: true}).click();
        await page.getByRole('searchbox', {name: 'Buscar organização ou contato', exact: true}).fill('Marcos');
        await page.getByRole('heading', {name: 'ACME Eventos', exact: true}).waitFor();
        assert.equal(await page.getByRole('heading', {name: 'Conexoes Corporate', exact: true}).count(), 0);
        await nav.getByRole('button', {name: 'Eventos', exact: true}).click();
        await page.getByRole('heading', {name: 'Happy Hour Conexoes', exact: true}).waitFor();
        await page.getByRole('button', {name:'Situação dos eventos',exact:true}).click();
        await page.getByRole('menuitemradio',{name:'Agendados',exact:true}).click();
        assert.equal(await page.getByRole('heading', {name: 'Happy Hour Conexoes', exact: true}).count(), 0);
        await page.getByRole('button', {name:'Situação dos eventos',exact:true}).click();
        await page.getByRole('menuitemradio',{name:'Todos',exact:true}).click();
        await page.getByRole('heading', {name: 'Happy Hour Conexoes', exact: true}).waitFor();
      }
      if (mode !== 'participant') await nav.getByRole('button', { name: 'Mais', exact: true }).click();
      if (mode === 'global') await page.getByRole('tab', {name:'Conta',exact:true}).click();
      const logout = page.getByRole('button', { name: 'Sair da conta', exact: true }).filter({ visible: true });
      await logout.waitFor();
      rejectLogout = true;
      await logout.click();
      await page.getByText('Falha temporaria ao sair.', { exact: false }).first().waitFor();
      assert(await nav.isVisible(), `logout failure must retain session: ${mode}`);
      rejectLogout = false;
      await logout.click();
      await page.getByLabel('E-mail', { exact: true }).waitFor({timeout: 5000}).catch(async error => {
        await page.screenshot({path: '.tools/ui-check/screenshots/logout-failure.png'});
        console.log(await page.locator('body').innerText());
        throw error;
      });
      assert.equal(logoutCalls, 2);
      assert.equal(await page.locator('.adm-bottom,.bottom-nav').count(), 0);
      await page.reload();
      await page.getByLabel('E-mail', { exact: true }).waitFor();
      assert.equal(loggedIn, false);
      await context.close();
      console.log(`${mode}: bottom menu, responsive layout, failed logout and successful logout verified.`);
    }
    const mockContext = await browser.newContext({ viewport: {width: 390, height: 844} });
    const mockPage = await mockContext.newPage();
    mockPage.on('pageerror', error => errors.push(`mock: ${error.message}`));
    let apiCalls = 0;
    mockPage.on('request', request => { if (new URL(request.url()).pathname.startsWith('/api/')) apiCalls++; });
    await mockPage.route('**/config.ts*', async route => {
      const response = await route.fetch();
      const source = await response.text();
      await route.fulfill({ response, body: source.replace(/const mode = [^;]+;/, 'const mode = "mock";') });
    });
    await mockPage.goto(MOCK_URL + '/#descobrir');
    await mockPage.locator('.bottom-nav').waitFor();
    for (const width of [320, 390, 768, 1440]) {
      await mockPage.setViewportSize({width, height: 844});
      for (const route of ['perfil', 'filtros', 'descobrir', 'mensagens', 'participantes']) {
        await mockPage.evaluate(route => { location.hash = route; }, route);
        await mockPage.locator('.bottom-nav [aria-current="page"]').waitFor();
        assert(await mockPage.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `mock overflow ${route} ${width}`);
        if (width === 390) await mockPage.screenshot({path: `.tools/ui-check/screenshots/navigation-mock-${route}.png`});
      }
    }
    await mockPage.locator('.bottom-nav').getByRole('button', {name: 'Perfil', exact: true}).click();
    await mockPage.getByRole('button', {name: 'Sair da conta', exact: true}).click();
    await mockPage.locator('.login-screen').waitFor();
    await mockPage.getByRole('button', {name: 'Explorar administração', exact: true}).click();
    await mockPage.locator('.adm-bottom').waitFor();
    await mockPage.locator('.adm-bottom').getByRole('button', {name: 'Mais', exact: true}).click();
    await mockPage.getByRole('button', {name: 'Sair da conta', exact: true}).filter({visible: true}).click();
    await mockPage.locator('.login-screen').waitFor();
    assert.equal(apiCalls, 0, 'mock mode must not call the backend');
    await mockContext.close();
    console.log('mock: five participant screens and both logout locations verified without backend calls.');
    assert.deepEqual(errors, []);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
