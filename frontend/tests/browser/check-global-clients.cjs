const { BASE_URL, MOCK_URL, launch, testCredentials } = require('./helpers.cjs');
const {chromium} = require('playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await launch();
  try {
    for (const width of [320, 390, 768, 1440]) {
      const context = await browser.newContext({viewport: {width, height: 900}});
      const page = await context.newPage();
      const errors = [], requests = [];
      const data = {staff: true, metrics: {}, clients: [], events: [], activity: [], alerts: [], safety: []};
      const clientId = 'e10c09d3-16a6-4d14-a7d9-f62a9bec66be';
      page.on('pageerror', error => errors.push(error.message));
      await page.route('**/api/**', async route => {
        const url = new URL(route.request().url());
        if (url.pathname === '/api/session/') return route.fulfill({json: {authenticated: true, csrfToken: 'test-token'}});
        if (url.pathname === '/api/bootstrap/') return route.fulfill({json: {navigation: 'global'}});
        if (url.pathname === '/api/global/' && route.request().method() === 'GET') return route.fulfill({json: data});
        if (url.pathname === '/api/global/' && route.request().method() === 'POST') {
          const body = route.request().postDataJSON(); requests.push(body);
          if (body.action === 'create_client') {
            assert.deepEqual(Object.keys(body).sort(), ['action', 'contact', 'email', 'phone']);
            data.clients.push({id: clientId, name: body.contact, contact: body.contact, email: body.email, phone: body.phone, description: '', active: true, draft: {...body}, team: [{id:'member-1',email:'owner@example.com',firstName:'Owner',lastName:'Test',active:true,role:'ADMIN',passwordConfigured:false}]});
            return route.fulfill({status: 201, json: {id: clientId, ok: true}});
          }
          if (body.action === 'update_client') {
            assert.equal(body.id, clientId);
            assert(!body.activate);
            data.clients[0] = {...data.clients[0], name: body.organization, contact: body.contact, email: body.email, phone: body.phone, description: body.description, draft: {...body}};
            return route.fulfill({json: {id: clientId, ok: true}});
          }
          if (body.action === 'create_event') {
            assert.equal(body.client, clientId);
            assert.equal(body.event, 'Evento de teste');
            assert.equal(body.responsible, 'owner@example.com');
            assert(new Date(body.ends) > new Date(body.starts));
            data.events.push({id: 'event-1', name: body.event, state: 'SCHEDULED', status: 'Agendado', organization: data.clients[0].name, organizationId: clientId});
            return route.fulfill({status: 201, json: {id: 'event-1', client: clientId, ok: true}});
          }
        }
        throw Error(`Unexpected request: ${url.pathname}`);
      });
      await page.goto(BASE_URL + '/', {waitUntil: 'networkidle'});
      await page.getByRole('button', {name: '+ Novo cliente', exact: true}).click();
      assert.equal(await page.locator('form input').count(), 3);
      assert.equal(await page.getByText(/de 6/).count(), 0);
      await page.getByLabel('Nome', {exact: true}).fill('Marcos Silva');
      await page.getByLabel('E-mail', {exact: true}).fill('marcos@example.com');
      await page.getByLabel('Telefone', {exact: true}).fill('+55 11 98765-4321');
      await page.getByRole('button', {name: 'Cadastrar cliente', exact: true}).click();
      await page.getByRole('heading', {name: 'Marcos Silva', exact: true}).waitFor();
      assert.equal(data.events.length, 0);
      await page.getByRole('button', {name: 'Completar / editar cadastro', exact: true}).click();
      assert.equal(await page.getByLabel('Telefone', {exact: true}).inputValue(), '+55 11 98765-4321');
      await page.getByLabel('Nome da organização', {exact: true}).fill('ACME Eventos');
      await page.getByLabel('Descrição da organização', {exact: true}).fill('Organização de eventos');
      await page.getByLabel('Cargo / função', {exact: true}).fill('Diretor');
      await page.getByRole('button', {name: 'Salvar alterações', exact: true}).click();
      await page.getByText('ACME Eventos', {exact: true}).waitFor();
      assert.equal(data.events.length, 0);
      assert.equal(data.clients.length, 1);
      const nav = page.locator('.adm-bottom');
      await nav.getByRole('button', {name: 'Eventos', exact: true}).click();
      assert.equal(await page.getByRole('button', {name: '+ Novo cliente', exact: true}).count(), 0);
      await page.getByRole('button', {name: '+ Novo evento', exact: true}).click();
      await page.getByLabel('Cliente', {exact: true}).selectOption(clientId);
      await page.getByLabel('Modalidade').selectOption('ONLINE');
      await page.getByLabel('Nome do evento', {exact: true}).fill('Evento de teste');
      await page.locator('form').getByLabel('Início', {exact: true}).fill('2026-10-05T18:00');
      await page.getByLabel('Término', {exact: true}).fill('2026-10-05T23:00');
      await page.getByLabel('E-mail da conta responsável', {exact: true}).selectOption('owner@example.com');
      await page.screenshot({path: `.tools/ui-check/screenshots/global-new-event-${width}.png`});
      await page.getByRole('button', {name: 'Criar evento', exact: true}).click();
      await page.getByRole('heading', {name: 'Evento de teste', exact: true}).waitFor();
      assert.equal(data.clients.length, 1);
      assert.equal(data.events.length, 1);
      assert.equal(requests.length, 3);
      await nav.getByRole('button', {name: 'Clientes', exact: true}).click();
      await page.getByRole('button', {name: 'Ver cliente', exact: true}).click();
      await page.getByText('Evento de teste · Agendado', {exact: true}).waitFor();
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await page.screenshot({path: `.tools/ui-check/screenshots/global-client-details-${width}.png`});
      assert.deepEqual(errors, []);
      await context.close();
      console.log(`${width}px: one-step client, detail editor, separate event creation and linked event verified.`);
    }
  } finally {await browser.close();}
})().catch(error => {console.error(error); process.exit(1);});
