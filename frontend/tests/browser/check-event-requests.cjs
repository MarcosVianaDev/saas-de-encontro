const { BASE_URL, MOCK_URL, launch, testCredentials } = require('./helpers.cjs');
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await launch();
  try {
    for (const width of [390, 1440]) {
      for (const navigation of ['administration', 'global']) {
        const context = await browser.newContext({ viewport: { width, height: 1000 } });
        const page = await context.newPage();
        page.setDefaultTimeout(10000);
        const errors = [];
        let submitted;
        page.on('pageerror', error => { errors.push(error.message); console.log('Page error:', error.stack); });
        const events = ['RUNNING', 'SCHEDULED', 'PAUSED', 'DRAFT', 'OPEN', 'CLOSED', 'ARCHIVED'].map((state, i) => ({
          id: `event-${i}`, name: `${state} event`, state, status: state, organization: 'Organization', organizationId: 'org', role: 'ADMIN',
        }));
        const admin = { role: 'ADMIN', globalContext: false, permissions: [], events: [{...events[0], name: 'Existing event'}, {...events[1], name: 'Another event'}],
          event: { id: events[0].id, name: 'Existing event', mode: 'ONLINE', state: 'RUNNING', description: '', starts: null, ends: null, status: 'Em andamento', joinPath: null, responsible: [] },
          participants: [], cases: [], blockSignals: [], team: [],
          metrics: { participants: 0, active: 0, new: 0, matches: 0, conversations: 0, blocks: 0 },
        };
        const global = { staff: true, metrics: { RUNNING: 1, SCHEDULED: 1, PAUSED: 1, DRAFT: 1 }, clients: [], events, safety: [], activity: [], alerts: [] };
        await page.route('**/api/**', async route => {
          const path = new URL(route.request().url()).pathname;
          if (path === '/api/session/') return route.fulfill({ json: { authenticated: true, csrfToken: 'test' } });
          if (path === '/api/bootstrap/') return route.fulfill({ json: { navigation, role: 'ADMIN' } });
          if (path === '/api/event-admin/') {
            if (route.request().method() === 'POST') {
              const selected = admin.events.find(event => event.id === route.request().postDataJSON().event);
              admin.event = {...admin.event, id: selected.id, name: selected.name};
            }
            return route.fulfill({ json: admin });
          }
          if (path === '/api/global/') return route.fulfill({ json: global });
          if (path === '/api/notifications/') return route.fulfill({ json: { items: [], unread: 0 } });
          if (path === '/api/event-admin/requests/') {
            submitted = route.request().postDataJSON();
            return route.fulfill({ status: 201, json: { id: 'new', state: 'DRAFT', pendingApproval: true } });
          }
          return route.fulfill({ json: [] });
        });
        await page.goto(BASE_URL + '/', { waitUntil: 'networkidle' });
        console.log('Checking', navigation, width, (await page.locator('body').innerText()).slice(0, 250));
        if (navigation === 'administration') {
          const selector = page.getByRole('button', {name: 'Selecionar evento', exact: true});
          await selector.getByText('Existing event', {exact: true}).waitFor();
          assert.equal(await page.locator('.event-admin-details strong').count(), 0);
          await selector.click();
          assert.equal(await page.getByRole('menuitemradio', {name: 'Existing event', exact: true}).getAttribute('aria-checked'), 'true');
          await page.getByRole('menuitemradio', {name: 'Another event', exact: true}).click();
          await selector.getByText('Another event', {exact: true}).waitFor();
          await page.waitForFunction(() => !document.querySelector('#event-selector').disabled);
          await selector.focus();
          await page.keyboard.press('ArrowDown');
          await page.getByRole('menu').waitFor();
          await page.keyboard.press('Escape');
          assert.equal(await selector.getAttribute('aria-expanded'), 'false');
          await page.getByRole('button', { name: 'Solicitar novo evento', exact: true }).click();
          const form = page.locator('.event-request-form');
          await form.getByLabel('Nome do evento', { exact: true }).fill('Requested event');
          await form.getByLabel('Descrição', { exact: true }).fill('Requested description');
          await form.getByLabel('Modalidade', { exact: true }).selectOption('ONLINE');
          assert.equal(await form.getByLabel('Latitude', { exact: true }).count(), 0);
          assert.equal(await form.getByLabel('Raio (metros)', { exact: true }).count(), 0);
          await form.getByLabel('Início', { exact: true }).fill('2026-11-10T18:00');
          await form.getByLabel('Término', { exact: true }).fill('2026-11-10T23:00');
          await form.getByLabel('Intervalo de localização (minutos)', { exact: true }).fill('20');
          await form.getByRole('switch', {name:/Ativar automaticamente/}).check();
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
          await form.getByRole('button', { name: /Salvar solicitação/ }).click();
          console.log('Submission', submitted, (await page.locator('body').innerText()).slice(0, 700));
          await page.getByRole('status').filter({ hasText: 'Evento salvo como rascunho.' }).waitFor();
          assert.equal(submitted.event, 'Requested event');
          assert.equal(submitted.auto_activate_participants, true);
          assert.equal(submitted.location_interval_minutes, '20');
          assert(!('state' in submitted));
        } else {
          assert.equal(await page.getByText('Clientes ativos', { exact: true }).count(), 0);
          assert.deepEqual(await page.locator('.global-event-stat span').allTextContents(), ['Eventos em andamento', 'Eventos agendados', 'Eventos pausados', 'Eventos solicitados']);
          for (const [state, label] of [['DRAFT', 'Eventos solicitados'], ['RUNNING', 'Eventos em andamento'], ['SCHEDULED', 'Eventos agendados'], ['PAUSED', 'Eventos pausados']]) {
            await page.getByRole('button', { name: new RegExp(label) }).click();
            const labels = { DRAFT: 'Rascunhos / solicitados', RUNNING: 'Em andamento', SCHEDULED: 'Agendados', PAUSED: 'Pausados' };
            assert.equal((await page.getByRole('button', { name: 'Situação dos eventos', exact: true }).innerText()).trim(), labels[state]);
            assert.equal(await page.locator('.global-content > section.adm-card h3').count(), 1);
            await page.locator('.adm-bottom').getByRole('button', { name: 'Início', exact: true }).click();
          }
          await page.getByRole('button', { name: /Eventos solicitados/ }).click();
          const toggle = page.getByRole('button', { name: 'Situação dos eventos', exact: true });
          await toggle.click();
          assert.equal(await page.getByRole('menuitemradio').count(), 8);
          await page.getByRole('menuitemradio', { name: 'Encerrados', exact: true }).click();
          assert.equal((await toggle.innerText()).trim(), 'Encerrados');
          assert.equal(await page.locator('.global-content > section.adm-card h3').innerText(), 'CLOSED event');
          await toggle.click();
          await page.getByRole('menuitemradio', { name: 'Todos', exact: true }).click();
          assert.equal(await page.locator('.global-content > section.adm-card h3').count(), 7);
          await toggle.focus();
          await page.keyboard.press('ArrowDown');
          await page.getByRole('menu').waitFor();
          await page.keyboard.press('Escape');
          assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
        }
        assert.deepEqual(errors, []);
        await context.close();
      }
    }
    console.log('OK: requester form and draft submission, hidden online GPS fields, global card filters, all statuses and responsive layout. API calls simulated.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
