const { BASE_URL, MOCK_URL, launch, testCredentials, selectEvent } = require('./helpers.cjs');
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
(async () => {
  const creds = testCredentials();
  const browser = await launch();
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await context.newPage();
    for (let i=0; i<30; i++) {
      const health = await page.request.get(BASE_URL + '/api/health/');
      if (health.ok()) break;
      await page.waitForTimeout(500);
    }
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.getByLabel('E-mail', { exact: true }).fill(creds.adminEmail);
    await page.getByLabel('Senha', { exact: true }).fill(creds.password);
    await page.locator('form').getByRole('button', { name: /Entrar/ }).click();
    await selectEvent(page);
    await page.screenshot({path:'.tools/ui-check/screenshots/admin-dashboard-desktop.png'});
    const nav = page.locator('.adm-bottom');
    await nav.getByRole('button',{name:'Participantes',exact:true}).click();
    await page.getByRole('heading',{name:'Participantes',exact:true}).waitFor();
    await page.getByRole('button',{name:'Filtros',exact:true}).click();
    await page.getByLabel('Situação',{exact:true}).selectOption('Cadastro incompleto');
    await page.getByRole('button',{name:'Limpar filtros',exact:true}).click();
    await page.getByRole('button',{name:'Aplicar',exact:true}).click();
    const count = await page.locator('.adm-person').count();
    assert(count > 0);
    await page.locator('.adm-person').first().click();
    await page.getByRole('heading',{name:'Ações administrativas'}).waitFor();
    await page.getByRole('button',{name:'Suspender do evento',exact:true}).click();
    await page.getByRole('dialog').waitFor();
    await page.getByRole('dialog').getByRole('button',{name:'Cancelar',exact:true}).click();
    await page.getByRole('button',{name:'Ocorrências',exact:true}).click();
    await page.getByRole('heading',{name:'Contexto administrativo'}).waitFor();
    await nav.getByRole('button',{name:/Moderação/}).click();
    await page.getByRole('heading',{name:'Moderação',exact:true}).waitFor();
    await nav.getByRole('button',{name:'Evento',exact:true}).click();
    await page.getByRole('button',{name:'Exibir QR Code',exact:true}).click();
    const qr = page.getByRole('img',{name:/QR Code de ingresso/});
    await qr.waitFor();
    await qr.evaluate(img => img.decode());
    const link = await page.getByLabel('URL de acesso ao evento').inputValue();
    assert(link.includes('?invite='));
    await page.addScriptTag({path:require.resolve('jsqr/dist/jsQR.js')});
    const decoded = await qr.evaluate(img => {
      const canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth; canvas.height = img.naturalHeight;
      const ctx = canvas.getContext('2d'); ctx.drawImage(img,0,0);
      const pixels = ctx.getImageData(0,0,canvas.width,canvas.height);
      return window.jsQR(pixels.data,canvas.width,canvas.height)?.data;
    });
    assert.equal(decoded,link,'QR must decode to the exact invitation URL');
    for (const width of [320,375,768,1440]) {
      await page.setViewportSize({width,height:1000});
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),`Overflow ${width}`);
      await page.screenshot({path:`.tools/ui-check/screenshots/admin-qr-${width}.png`});
      for (const route of ['dashboard','participants','moderation','event','more','team','report']) {
        await page.evaluate(r => {location.hash=`admin-${r}`},route);
        await page.waitForTimeout(100);
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),`Overflow ${route} ${width}`);
        if (width === 375) await page.screenshot({path:`.tools/ui-check/screenshots/admin-${route}-mobile.png`});
      }
      await page.evaluate(() => {location.hash='admin-qr'});
      await page.getByLabel('URL de acesso ao evento').waitFor();
    }
    await page.reload({waitUntil:'networkidle'});
    await page.locator('.adm-workspace').waitFor();
    const guestContext = await browser.newContext({viewport:{width:375,height:900}});
    const guest = await guestContext.newPage();
    await guest.goto(link,{waitUntil:'networkidle'});
    await guest.getByRole('heading',{name:/Participar de/}).waitFor();
    await guest.getByLabel('E-mail',{exact:true}).fill(creds.email);
    await guest.getByLabel('Senha',{exact:true}).fill(creds.password);
    await guest.locator('form').getByRole('button',{name:/Entrar/}).click();
    await guest.waitForURL('**/#perfil');
    const data = await guest.evaluate(async () => (await fetch('/api/bootstrap/')).json());
    assert.equal(data.navigation,'participant');
    assert.equal(data.event.name,'Conecta São Paulo');
    assert.deepEqual(errors,[]);
    console.log('PASS: admin login, screens, filters, QR link, session restore, responsive layouts, guest invite login.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
