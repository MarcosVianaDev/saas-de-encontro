const { BASE_URL, MOCK_URL, launch, testCredentials, selectEvent } = require('./helpers.cjs');
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
(async () => {
  const creds = testCredentials();
  const origin = process.env.TEST_LAN_URL || BASE_URL;
  const browser = await launch();
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(origin,{waitUntil:'networkidle'});
    await page.getByLabel('E-mail',{exact:true}).fill(creds.adminEmail);
    await page.getByLabel('Senha',{exact:true}).fill(creds.password);
    await page.locator('form').getByRole('button',{name:/Entrar/}).click();
    await selectEvent(page);
    await page.getByRole('button',{name:/Exibir QR Code de acesso/}).click();
    const url=await page.getByLabel('URL de acesso ao evento').inputValue();
    assert(url.startsWith(origin+'/?invite='));
    const health=await context.request.get(origin+'/api/health/');assert.equal(health.status(),200);
    const session=(await (await context.request.get(origin+'/api/session/')).json());
    const foreign=await context.request.post(origin+'/api/auth/logout/',{headers:{Origin:'http://unrelated.example','X-CSRFToken':session.csrfToken}});
    assert.equal(foreign.status(),403,'Foreign origin must still be rejected');
    const logout=await context.request.post(origin+'/api/auth/logout/',{headers:{Origin:origin,'X-CSRFToken':session.csrfToken}});
    assert.equal(logout.status(),200,'LAN same-origin CSRF must succeed');
    assert.deepEqual(errors,[]);
    console.log('PASS: page, admin login, API health, QR uses the tested origin, same-origin POST accepted and foreign-origin POST rejected.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
