const assert = require('node:assert/strict');
const { BASE_URL, launch, mockSync } = require('./helpers.cjs');

(async () => {
  const browser = await launch();
  try {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const people = ['Mulheres', 'Homens', 'Não binário', 'Prefiro não informar'].map((gender, index) => ({
      id: String(index), name: `Pessoa ${index}`, age: 30, gender, job: '',
      image: '/images/profile-placeholder.svg', interests: [], online: true, mutual: false,
    }));
    const data = { navigation: 'participant', onboardingComplete: true, active: true, socialAvailable: true,
      profile: { first: 'Pessoa', last: 'Teste', month: '1', year: '1995', gender: 'Mulheres',
        bio: 'Um perfil preenchido para testar as escolhas de gênero nos filtros.', interests: [], purpose: '' },
      photos: [], filters: { min: 18, max: 35, gender: 'Todos', interests: [], purpose: '' },
      people, discovery: people, chats: {}, chatStates: {}, seen: [], liked: [], saved: [],
      event: { id: 'gender-test', name: 'Evento', state: 'RUNNING', mode: 'ONLINE' } };
    let saves = 0;
    await page.route('**/api/**', async route => {
      const path = new URL(route.request().url()).pathname;
      let body = {};
      if (path === '/api/session/') body = { authenticated: true, csrfToken: 'test' };
      else if (path === '/api/bootstrap/') body = data;
      else if (path === '/api/sync/') body = mockSync(data);
      else if (path === '/api/catalog/') body = { people, discovery: data.discovery };
      else if (path === '/api/filters/') {
        const submitted = route.request().postDataJSON();
        assert.equal(submitted.gender, 'Todos');
        assert.equal('genders' in submitted, false);
        data.filters = submitted;
        saves++;
        body = data;
      } else if (path === '/api/interactions/0/') {
        data.seen = ['0'];
        data.discovery = people.slice(1);
        body = { match: null, data };
      } else if (path === '/api/notifications/') body = { items: [], unread: 0 };
      else if (path === '/api/support/') body = [];
      else if (path === '/api/health/') body = { status: 'ok' };
      await route.fulfill({ json: body });
    });
    await page.goto(BASE_URL + '/#filtros');
    const option = name => page.getByRole('button', { name, exact: true });
    await option('Não binários').waitFor();
    assert.equal(await option('Todos').getAttribute('aria-pressed'), 'true');
    await option('Mulheres').click();
    await option('Não binários').click();
    for (const name of ['Mulheres', 'Não binários']) assert.equal(await option(name).getAttribute('aria-pressed'), 'true');
    assert.equal(await option('Homens').getAttribute('aria-pressed'), 'false');
    assert.match(await page.locator('.filter-summary').innerText(), /2 pessoas/);
    await option('Aplicar filtros').click();
    await option('Passar Pessoa 0').waitFor();
    assert.equal(saves, 1);
    assert.match(await page.locator('.discovery-meta').innerText(), /2 para/);
    await option('Passar Pessoa 0').click();
    await option('Passar Pessoa 2').waitFor();
    await page.reload();
    await option('Passar Pessoa 2').waitFor();
    await option('Alterar filtros').click();
    for (const name of ['Mulheres', 'Não binários']) assert.equal(await option(name).getAttribute('aria-pressed'), 'true');
    await option('Mulheres').click();
    assert.match(await page.locator('.filter-summary').innerText(), /1 pessoas/);
    await option('Não binários').click();
    assert.equal(await option('Todos').getAttribute('aria-pressed'), 'true');
    assert.match(await page.locator('.filter-summary').innerText(), /4 pessoas/);
    await option('Homens').click();
    await option('Não binários').click();
    assert.match(await page.locator('.filter-summary').innerText(), /2 pessoas/);
    await option('Todos').click();
    assert.equal(await option('Homens').getAttribute('aria-pressed'), 'false');
    assert.equal(await option('Não binários').getAttribute('aria-pressed'), 'false');
    assert.deepEqual(errors, []);
    await context.close();
    console.log('PASS: multiple genders, nonbinary discovery, broad API query, preserved selection after decisions/reload and all-gender reset.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
