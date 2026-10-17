const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { launch, login, api, testCredentials } = require('./helpers.cjs');

(async () => {
  assert(process.env.TEST_BACKEND_CONTAINER, 'Use the disposable browser runner.');
  const browser = await launch();
  const errors = [];
  try {
    const admin = await browser.newPage({ viewport: { width: 320, height: 900 } });
    admin.on('pageerror', error => errors.push(error.message));
    await login(admin, testCredentials().adminEmail);
    await admin.locator('.adm-bottom').getByRole('button', { name: 'Mais', exact: true }).click();
    await admin.getByRole('tab', { name: 'Participantes', exact: true }).click();
    const orientation = admin.locator('article').filter({ has: admin.getByText('Orientação', { exact: true }) });
    await orientation.getByRole('button', { name: 'Editar', exact: true }).click();
    assert.match(await admin.getByRole('textbox', { name: 'Opções', exact: true }).inputValue(), /Heterossexual, Homossexual, Bissexual/);
    assert.equal(await admin.getByRole('switch', { name: 'Exibir no filtro', exact: true }).isChecked(), true);
    const mode = admin.getByRole('switch', { name: 'Escolha múltipla no filtro', exact: true });
    assert.equal(await mode.isChecked(), false);
    assert.equal(await admin.locator('.topic-filter-choice .selected').innerText(), 'Escolha única');
    await mode.check();
    assert.equal(await admin.locator('.topic-filter-choice .selected').innerText(), 'Escolha múltipla');
    await mode.uncheck();
    await admin.getByRole('button', { name: 'Salvar', exact: true }).click();
    await admin.getByRole('button', { name: '+ Novo tópico', exact: true }).click();
    await admin.getByLabel('Nome do tópico', { exact: true }).fill('Idiomas para filtrar');
    await admin.getByRole('textbox', { name: 'Opções', exact: true }).fill('Português, Inglês');
    assert.equal(await admin.getByRole('group', { name: 'Tipo de escolha no filtro' }).count(), 0);
    await admin.getByRole('switch', { name: 'Exibir no filtro', exact: true }).check();
    await mode.check();
    assert.equal(await admin.getByRole('switch', { name: 'Permitir múltipla escolha', exact: true }).isChecked(), false);
    assert.equal(await admin.locator('.topic-filter-choice .selected').innerText(), 'Escolha múltipla');
    assert.equal(await admin.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await admin.getByRole('button', { name: 'Salvar', exact: true }).click();
    const topic = (await api(admin, 'global/')).topics.find(item => item.name === 'Idiomas para filtrar');
    assert(topic?.showInFilter && topic.filterMultiple && !topic.multiple);

    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const participant = await context.newPage();
    participant.on('pageerror', error => errors.push(error.message));
    await login(participant, testCredentials().email);
    const initial = await api(participant, 'filters/', 'PUT', {
      min: 18, max: 100, gender: 'Todos', interests: [], purpose: '', topics: {},
    });
    assert(initial.discovery.length >= 2);
    const [first, second] = initial.discovery;
    const fixture = { key: topic.key, first: String(first.id), second: String(second.id) };
    execFileSync('docker', ['exec', '-i', process.env.TEST_BACKEND_CONTAINER, 'python', 'manage.py', 'shell'], {
      input: `
import json
from apps.profiles.models import ParticipantProfile
data = json.loads(${JSON.stringify(JSON.stringify(fixture))})
for identifier, orientation, language in [(data['first'], 'Heterossexual', 'Português'), (data['second'], 'Bissexual', 'Inglês')]:
    profile = ParticipantProfile.objects.get(participant_id=identifier)
    profile.topic_answers = {**profile.topic_answers, 'orientation': [orientation], data['key']: [language]}
    profile.save(update_fields=['topic_answers'])
`, encoding: 'utf8',
    });
    await participant.goto(new URL('/#filtros', participant.url()).href);
    const filter = name => participant.getByRole('region', { name, exact: true });
    const option = (name, value) => filter(name).getByRole('button', { name: value, exact: true });
    await option('Orientação', 'Não filtrar').waitFor();
    assert.equal(await option('Orientação', 'Não filtrar').getAttribute('aria-pressed'), 'true');
    await option('Orientação', 'Heterossexual').click();
    await option('Orientação', 'Bissexual').click();
    assert.equal(await option('Orientação', 'Heterossexual').getAttribute('aria-pressed'), 'false');
    await option('Idiomas para filtrar', 'Português').click();
    await option('Idiomas para filtrar', 'Inglês').click();
    assert.equal(await option('Idiomas para filtrar', 'Português').getAttribute('aria-pressed'), 'true');
    assert.equal(await option('Idiomas para filtrar', 'Inglês').getAttribute('aria-pressed'), 'true');
    assert.match(await participant.locator('.filter-summary').innerText(), /1 pessoas/);
    await participant.getByRole('button', { name: 'Aplicar filtros', exact: true }).click();
    await participant.waitForURL('**/#descobrir');
    const saved = await api(participant, 'bootstrap/');
    assert.deepEqual(saved.discovery.map(person => person.id), [second.id]);
    assert.deepEqual(saved.filters.topics[topic.key], ['Português', 'Inglês']);
    await participant.reload();
    // The cached hash renders navigation before the session/bootstrap finishes.
    await participant.locator('.backend-ribbon').waitFor({ state: 'hidden' });
    await participant.getByRole('button', { name: 'Alterar filtros', exact: true }).click();
    await participant.getByRole('heading', { name: 'Definir filtros', exact: true }).waitFor();
    assert.equal(await option('Orientação', 'Bissexual').getAttribute('aria-pressed'), 'true');
    await option('Orientação', 'Não filtrar').click();
    await option('Idiomas para filtrar', 'Não filtrar').click();
    await participant.getByRole('button', { name: 'Aplicar filtros', exact: true }).click();
    await participant.waitForURL('**/#descobrir');
    assert.deepEqual((await api(participant, 'bootstrap/')).discovery.map(person => person.id), initial.discovery.map(person => person.id));

    await admin.locator('article').filter({ has: admin.getByText('Idiomas para filtrar', { exact: true }) })
      .getByRole('button', { name: 'Editar', exact: true }).click();
    await admin.getByRole('switch', { name: 'Exibir no filtro', exact: true }).uncheck();
    assert.equal(await admin.getByRole('group', { name: 'Tipo de escolha no filtro' }).count(), 0);
    await admin.getByRole('button', { name: 'Salvar', exact: true }).click();
    await participant.evaluate(() => { location.hash = 'filtros'; });
    await participant.reload();
    await option('Orientação', 'Não filtrar').waitFor();
    assert.equal(await filter('Idiomas para filtrar').count(), 0);
    await participant.evaluate(() => { location.hash = 'perfil'; });
    const profileOrientation = participant.locator('fieldset').filter({ has: participant.locator('legend', { hasText: /^Orientação$/ }) });
    await profileOrientation.getByRole('button', { name: 'Bissexual', exact: true }).click();
    await participant.getByRole('button', { name: 'Continuar', exact: true }).click();
    await participant.waitForURL('**/#descobrir');
    assert.deepEqual((await api(participant, 'bootstrap/')).profile.topicAnswers.orientation, ['Bissexual']);
    assert.deepEqual(errors, []);
    await context.close();
    console.log('PASS: global topic toggles/highlight, independent filter cardinality, seeded/editable orientation, real discovery filtering, persistence, no-filter reset, hidden filters and participant profile save.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
