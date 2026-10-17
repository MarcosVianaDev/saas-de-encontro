const assert = require('node:assert/strict');
const { BASE_URL, MOCK_URL, launch } = require('./helpers.cjs');

(async () => {
  const browser = await launch();
  const errors = [];
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`${MOCK_URL}/#participantes`);
    const nav = page.locator('.bottom-nav');
    await page.locator('.participant-tile').first().waitFor();
    assert.equal(await page.locator('.participant-tile').count(), 50);
    await page.getByLabel('Buscar participantes', { exact: true }).fill('No participant has this name');
    await page.getByRole('heading', { name: 'Ninguém por aqui' }).waitFor();
    await nav.getByRole('button', { name: 'Mensagens', exact: true }).click();
    await page.locator('.conversation-row').first().waitFor();
    await page.goBack();
    await page.getByRole('heading', { name: 'Participantes', exact: true }).waitFor();
    assert.equal(await page.getByLabel('Buscar participantes', { exact: true }).inputValue(), '');
    await page.goForward();
    await page.locator('.conversation-row').first().click();
    await page.getByLabel('Mensagem', { exact: true }).fill('Mensagem de teste das páginas separadas.');
    await page.getByRole('button', { name: 'Enviar mensagem', exact: true }).click();
    await page.getByText('Mensagem de teste das páginas separadas.', { exact: true }).waitFor();
    assert.equal(await page.getByLabel('Mensagem', { exact: true }).inputValue(), '');

    await nav.getByRole('button', { name: 'Descobrir', exact: true }).click();
    await page.getByRole('button', { name: 'Alterar filtros', exact: true }).click();
    const gender = page.locator('.filter-card').filter({ has: page.getByRole('heading', { name: 'Gênero', exact: true }) });
    await gender.getByRole('button', { name: 'Homens', exact: true }).click();
    assert(page.url().endsWith('#filtros'), 'Selecting a chip must not submit the form.');
    await nav.getByRole('button', { name: 'Descobrir', exact: true }).click();
    await page.getByRole('button', { name: 'Alterar filtros', exact: true }).click();
    assert.equal(await gender.getByRole('button', { name: 'Todos', exact: true }).getAttribute('aria-pressed'), 'true');
    await gender.getByRole('button', { name: 'Homens', exact: true }).click();
    await page.getByRole('button', { name: 'Aplicar filtros', exact: true }).click();
    await page.getByRole('heading', { name: 'Descobrir pessoas', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Alterar filtros', exact: true }).click();
    assert.equal(await gender.getByRole('button', { name: 'Homens', exact: true }).getAttribute('aria-pressed'), 'true');
    await nav.getByRole('button', { name: 'Perfil', exact: true }).click();
    const biography = page.locator('.bio-field textarea');
    assert.equal(await biography.getAttribute('minlength'), '50');
    assert.equal(await biography.getAttribute('maxlength'), '200');

    const demo = await browser.newPage();
    demo.on('pageerror', error => errors.push(error.message));
    await demo.goto(`${BASE_URL}/?demo=1#login`);
    await demo.getByLabel('E-mail', { exact: true }).waitFor();
    assert(await demo.getByLabel('E-mail', { exact: true }).inputValue());
    assert(await demo.getByLabel('Senha', { exact: true }).inputValue());
    await demo.evaluate(() => { location.hash = 'participantes'; });
    await demo.waitForURL(/#login$/);
    await demo.getByLabel('E-mail', { exact: true }).waitFor();
    assert.equal(await demo.locator('.participant-tile').count(), 0);

    const login = await browser.newPage();
    login.on('pageerror', error => errors.push(error.message));
    await login.route('**/api/**', route => {
      const path = new URL(route.request().url()).pathname;
      if (path === '/api/session/') return route.fulfill({ json: { authenticated: false, csrfToken: 'test' } });
      if (path === '/api/auth/login/') return route.fulfill({ status: 400, json: {
        email: ['Informe um e-mail válido.'], bio: ['Descrição inválida.'],
      } });
      throw Error(`Unexpected endpoint ${path}`);
    });
    await login.goto(`${BASE_URL}/#login`);
    await login.getByLabel('E-mail', { exact: true }).fill('test@example.invalid');
    await login.getByLabel('Senha', { exact: true }).fill('Test-password!');
    await login.getByRole('button', { name: 'Entrar', exact: true }).click();
    await login.getByText('E-mail: Informe um e-mail válido. Sobre você: Descrição inválida.', { exact: true }).waitFor();
    assert.deepEqual(errors, []);
    console.log('Participant pages: hash history, local drafts, messages, biography limits, login guard and field errors verified.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
