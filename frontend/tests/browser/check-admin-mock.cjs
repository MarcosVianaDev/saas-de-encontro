const { BASE_URL, MOCK_URL, launch, testCredentials } = require('./helpers.cjs');
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await launch();
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  const page=await context.newPage();
  const errors=[],calls=[];
  page.on('pageerror',e=>errors.push(e.message));
  await context.route('**/api/**',route=>{calls.push(route.request().url());return route.abort();});
  await page.goto(MOCK_URL + '/#admin-dashboard',{waitUntil:'networkidle'});
  await page.locator('.adm-hero').waitFor();
  assert.equal(await page.locator('.adm-stat strong').first().innerText(),'50');
  const nav=page.locator('.adm-bottom');
  await nav.getByRole('button',{name:'Participantes',exact:true}).click();
  await page.locator('.adm-person').filter({hasText:'Camila Souza'}).click();
  await page.getByRole('button',{name:'Suspender do evento',exact:true}).click();
  await page.getByRole('dialog').getByRole('textbox').fill('Suspensão fictícia para teste.');
  await page.getByRole('dialog').getByRole('button',{name:'Confirmar',exact:true}).click();
  await page.locator('.adm-profile .adm-badge').filter({hasText:'Suspenso'}).waitFor();
  await page.getByRole('button',{name:'Reativar participante',exact:true}).click();
  await page.getByRole('dialog').getByRole('textbox').fill('Reativação fictícia para teste.');
  await page.getByRole('dialog').getByRole('button',{name:'Confirmar',exact:true}).click();
  await page.locator('.adm-profile .adm-badge').filter({hasText:'Ativo'}).waitFor();
  await nav.getByRole('button',{name:'Moderação',exact:true}).click();
  await page.locator('.adm-case').filter({hasText:'DEMO-00001'}).click();
  await page.getByRole('button',{name:'Assumir caso',exact:true}).click();
  await page.getByRole('dialog').getByRole('button',{name:'Confirmar',exact:true}).click();
  await page.getByRole('button',{name:'Adicionar nota',exact:true}).click();
  await page.getByRole('dialog').getByRole('textbox').fill('Nota fictícia adicionada no navegador.');
  await page.getByRole('dialog').getByRole('button',{name:'Confirmar',exact:true}).click();
  await page.locator('.adm-main').getByText('Nota fictícia adicionada no navegador.',{exact:true}).waitFor();
  await page.getByRole('button',{name:'Arquivar sem ação',exact:true}).click();
  await page.getByRole('dialog').getByRole('combobox').selectOption('Situação resolvida');
  await page.getByRole('dialog').getByRole('textbox').fill('Exemplo concluído.');
  await page.getByRole('dialog').getByRole('button',{name:'Confirmar',exact:true}).click();
  await page.getByRole('button',{name:'Reabrir ocorrência',exact:true}).waitFor();
  await page.getByRole('button',{name:'Reabrir ocorrência',exact:true}).click();
  await page.getByRole('dialog').getByRole('textbox').fill('Nova evidência fictícia.');
  await page.getByRole('dialog').getByRole('button',{name:'Confirmar',exact:true}).click();
  await page.getByRole('button',{name:'Histórico',exact:true}).click();
  await page.getByText('Ocorrência reaberta: Nova evidência fictícia.',{exact:true}).waitFor();
  await nav.getByRole('button',{name:'Evento',exact:true}).click();
  await page.getByRole('button',{name:'Exibir QR Code',exact:true}).click();
  const link=await page.getByLabel('URL de acesso ao evento').inputValue();
  assert(link.includes('?demoEvent=demo-current'));
  const guest=await context.newPage();await guest.goto(link,{waitUntil:'networkidle'});
  await guest.getByText('Demonstração · Ingresso em Evento Conexões 2026',{exact:true}).waitFor();
  await guest.close();
  await page.getByRole('button',{name:'Selecionar evento',exact:true}).click(); await page.getByRole('menuitemradio',{name:'Encontro de Primavera',exact:true}).click();
  await page.getByText('Encontro de Primavera',{exact:true}).last().waitFor();
  assert.equal(await page.getByRole('button',{name:/Exibir QR Code de acesso/}).count(),0);
  await page.getByRole('button',{name:'Selecionar evento',exact:true}).click(); await page.getByRole('menuitemradio',{name:'Próximo Encontro',exact:true}).click();
  await page.getByText('Próximo Encontro',{exact:true}).last().waitFor();
  await page.getByRole('button',{name:'Selecionar evento',exact:true}).click(); await page.getByRole('menuitemradio',{name:'Evento Conexões 2026',exact:true}).click();
  await page.getByLabel('Papel de demonstração').selectOption('OPERATOR');
  assert.equal(await nav.getByRole('button',{name:'Moderação',exact:true}).count(),0);
  await page.getByLabel('Papel de demonstração').selectOption('MODERATOR');
  await nav.getByRole('button',{name:'Participantes',exact:true}).click();
  await page.locator('.adm-person').filter({hasText:'Camila Souza'}).click();
  assert.equal(await page.getByRole('button',{name:'Remover acesso ao evento',exact:true}).count(),0);
  await page.getByLabel('Papel de demonstração').selectOption('ADMIN');
  await page.getByRole('button',{name:'Restaurar demonstração',exact:true}).click();
  for(const width of [320,375,768,1440]){
   await page.setViewportSize({width,height:1000});
   for(const route of ['dashboard','participants','moderation','event','qr','team','report']){
    await page.evaluate(r=>location.hash='admin-'+r,route);await page.waitForTimeout(100);
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${route} ${width}`);
    if(width===375)await page.screenshot({path:'.tools/ui-check/screenshots/mock-admin-'+route+'.png'});
   }
  }
  await page.reload({waitUntil:'networkidle'});await page.locator('.adm-workspace').waitFor();
  await page.getByRole('button',{name:'Explorar participante',exact:true}).click();
  await page.getByRole('button',{name:'Explorar administração',exact:true}).waitFor();
  assert.deepEqual(calls,[],'Mock screens must not call backend');assert.deepEqual(errors,[]);
  console.log('PASS: mock fixtures, moderation actions, roles, event states, QR, navigation, responsive screens, no backend calls.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
