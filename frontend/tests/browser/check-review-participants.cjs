const assert = require('node:assert/strict');
const { BASE_URL, launch, mockSync } = require('./helpers.cjs');

(async () => {
  const browser = await launch();
  try {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const person = { id: 'passed', name: 'Pessoa reavaliada', age: 30, gender: 'Mulheres',
      job: '', image: '/images/profile-placeholder.svg', interests: [], online: true, mutual: false };
    const data = { navigation: 'participant', onboardingComplete: true, active: true, socialAvailable: true,
      profile: { first: 'Pessoa', last: 'Teste', month: '1', year: '1995', gender: 'Mulheres',
        bio: 'Um perfil preenchido para testar a revisão de participantes na descoberta.', interests: [], purpose: '' },
      photos: [], filters: { min: 18, max: 35, gender: 'Todos', interests: [], purpose: '' },
      people: [person], discovery: [], chats: {}, chatStates: {}, seen: ['passed', 'liked'], liked: ['liked'], saved: [],
      event: { id: 'review-test', name: 'Evento', state: 'RUNNING', mode: 'ONLINE' } };
    let reviews = 0;
    let passes = 0;
    await page.route('**/api/**', async route => {
      const path = new URL(route.request().url()).pathname;
      let body = {};
      if (path === '/api/session/') body = { authenticated: true, csrfToken: 'test' };
      else if (path === '/api/bootstrap/') body = data;
      else if (path === '/api/sync/') body = mockSync(data);
      else if (path === '/api/catalog/') body = { people: data.people, discovery: data.discovery };
      else if (path === '/api/discovery/review/') {
        assert.equal(route.request().method(), 'POST');
        reviews++;
        data.discovery = [person];
        data.seen = ['liked'];
        body = { count: 1, data };
      } else if (path === '/api/interactions/passed/') {
        assert.equal(route.request().postDataJSON().decision, 'PASS');
        passes++;
        data.discovery = [];
        data.seen = ['passed', 'liked'];
        body = { match: null, data };
      } else if (path === '/api/notifications/') body = { items: [], unread: 0 };
      else if (path === '/api/support/') body = [];
      else if (path === '/api/health/') body = { status: 'ok' };
      await route.fulfill({ json: body });
    });
    await page.goto(BASE_URL + '/#descobrir');
    await page.getByRole('button', { name: 'Rever participantes', exact: true }).click();
    await page.getByRole('button', { name: 'Passar Pessoa reavaliada', exact: true }).waitFor();
    assert.equal(reviews, 1);
    await page.reload();
    await page.getByRole('button', { name: 'Passar Pessoa reavaliada', exact: true }).click();
    await page.getByRole('button', { name: 'Rever participantes', exact: true }).waitFor();
    assert.equal(passes, 1);
    await page.getByRole('button', { name: 'Rever participantes', exact: true }).click();
    await page.getByRole('button', { name: 'Curtir Pessoa reavaliada', exact: true }).waitFor();
    assert.equal(reviews, 2);
    assert.deepEqual(errors, []);
    await context.close();
    console.log('PASS: empty discovery offers review, restores PASS cards, survives reload and allows another review.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
