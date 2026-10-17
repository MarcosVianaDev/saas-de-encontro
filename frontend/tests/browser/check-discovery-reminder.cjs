const assert = require('node:assert/strict');
const { BASE_URL, launch, mockSync } = require('./helpers.cjs');

(async () => {
  const browser = await launch();
  try {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const people = [
      ['woman', 'Mulheres', 170, 30, 'Tecnologia'],
      ['nonbinary', 'Não binário', 180, 30, 'Tecnologia'],
      ['man', 'Homens', 170, 30, 'Tecnologia'],
      ['short', 'Mulheres', 150, 30, 'Tecnologia'],
      ['older', 'Mulheres', 170, 50, 'Tecnologia'],
      ['different', 'Mulheres', 170, 30, 'Arte'],
    ].map(([id, gender, height, age, interest]) => ({
      id, name: id, age, gender, height, interests: [interest], job: '',
      image: '/images/profile-placeholder.svg', online: true, mutual: false,
    }));
    const data = { navigation: 'participant', onboardingComplete: true, active: true, socialAvailable: true,
      profile: { first: 'Pessoa', last: 'Teste', month: '1', year: '1995', gender: 'Mulheres',
        bio: 'Um perfil completo para testar o contador de pessoas compatíveis.', interests: [], purpose: '' },
      filters: { min: 18, max: 35, gender: 'Todos', minHeight: 160, maxHeight: 180,
        interests: ['Tecnologia'], topics: { interests: ['Tecnologia'] }, purpose: '' },
      profileTopics: [{ id: 'interests', key: 'interests', name: 'Interesses', multiple: true,
        options: ['Tecnologia', 'Arte'], showInFilter: true, filterMultiple: true }],
      photos: [], people, discovery: people.slice(0, 2), chats: {}, chatStates: {}, seen: [], liked: [], saved: [],
      event: { id: 'reminder-event', name: 'Evento', state: 'RUNNING', mode: 'ONLINE' } };
    let catalogCalls = 0;
    let available = people;
    await page.route('**/api/**', async route => {
      const path = new URL(route.request().url()).pathname;
      let body = {};
      if (path === '/api/session/') body = { authenticated: true, csrfToken: 'test' };
      else if (path === '/api/bootstrap/') body = data;
      else if (path === '/api/sync/') body = mockSync(data);
      else if (path === '/api/catalog/') {
        catalogCalls++;
        body = { people: available, discovery: data.discovery, profileTopics: data.profileTopics };
      } else if (path === '/api/notifications/') body = { items: [], unread: 0 };
      else if (path === '/api/support/') body = [];
      else if (path === '/api/health/') body = { status: 'ok' };
      await route.fulfill({ json: body });
    });
    await page.addInitScript(() => {
      sessionStorage.setItem('eventconnect-gender-filters:reminder-event', JSON.stringify(['Mulheres', 'Não binário']));
    });
    await page.clock.install({ time: new Date('2026-10-17T12:00:00Z') });
    await page.clock.pauseAt(new Date('2026-10-17T12:00:01Z'));
    await page.goto(BASE_URL + '/#descobrir');
    const menu = label => page.locator('.bottom-nav').getByRole('button', { name: label, exact: true });
    const badge = page.locator('.nav-discovery-count');
    await menu('Perfil').click();
    const visitKey = 'eventconnect-discovery-last-access:reminder-event';
    assert(Number(await page.evaluate(key => localStorage.getItem(key), visitKey)) > 0);
    const before = catalogCalls;
    await page.clock.fastForward(599000);
    assert.equal(await badge.count(), 0);
    assert.equal(catalogCalls, before, 'No reminder request before ten minutes on the profile page');
    await page.clock.fastForward(1000);
    await page.waitForFunction(() => document.querySelector('.nav-discovery-count')?.textContent === '2');
    assert(catalogCalls > before);
    await page.evaluate(() => { location.hash = 'filtros'; });
    await page.locator('.filter-summary').waitFor();
    assert.match(await page.locator('.filter-summary').innerText(), /2 pessoas/);
    await page.getByRole('slider', { name: 'Idade máxima' }).press('Home');
    assert.match(await page.locator('.filter-summary').innerText(), /0 pessoas/);
    assert.equal(await badge.innerText(), '2', 'Badge uses applied preferences, not unsaved filter edits');
    await menu('Descobrir').click();
    const explanation = page.getByRole('status').filter({ hasText: '2 pessoas ainda combinam com suas preferências.' });
    await explanation.waitFor();
    assert.equal(await badge.count(), 0);
    await page.clock.fastForward(4000);
    await explanation.waitFor({ state: 'hidden' });
    await menu('Perfil').click();
    const secondVisit = await page.evaluate(key => localStorage.getItem(key), visitKey);
    await page.clock.fastForward(600000);
    await page.waitForFunction(() => document.querySelector('.nav-discovery-count')?.textContent === '2');
    await page.reload();
    await page.waitForFunction(() => document.querySelector('.nav-discovery-count')?.textContent === '2');
    assert.equal(await page.evaluate(key => localStorage.getItem(key), visitKey), secondVisit);
    await menu('Descobrir').click();
    assert.equal(await explanation.count(), 0, 'The explanation does not repeat after reload');
    await menu('Perfil').click();
    await page.evaluate(() => {
      window.testHidden = true;
      Object.defineProperty(document, 'hidden', { configurable: true, get: () => window.testHidden });
      document.dispatchEvent(new Event('visibilitychange'));
    });
    const hiddenCalls = catalogCalls;
    await page.clock.fastForward(600000);
    assert.equal(catalogCalls, hiddenCalls);
    assert.equal(await badge.count(), 0);
    await page.evaluate(() => { window.testHidden = false; document.dispatchEvent(new Event('visibilitychange')); });
    await page.waitForFunction(() => document.querySelector('.nav-discovery-count')?.textContent === '2');
    available = [];
    await page.clock.fastForward(60000);
    await badge.waitFor({ state: 'hidden' });
    data.event = { ...data.event, id: 'other-reminder-event' };
    await page.reload();
    await menu('Perfil').waitFor();
    assert.equal(await badge.count(), 0, 'Another event starts its own timer');
    assert.deepEqual(errors, []);
    await context.close();
    console.log('PASS: ten-minute threshold, current matching count, applied filters, persistent access time, one-time explanation, visibility and event isolation.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
