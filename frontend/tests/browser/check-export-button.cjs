const {BASE_URL,launch}=require('./helpers.cjs');
const assert=require('node:assert/strict');
(async()=>{
const browser=await launch();
try {
  const page=await browser.newPage();const errors=[];let requests=0,polls=0,completed=false;
  page.on('pageerror',e=>errors.push(e.message));
  const pending={id:'export-1',state:'PENDING',progress:0,stage:'Aguardando Celery',expires:null};
  const data={role:'ADMIN',globalContext:true,permissions:[],events:[],event:{id:'event-1',name:'Evento de teste',state:'RUNNING',mode:'ONLINE',status:'Em andamento',responsible:[]},participants:[],cases:[],blockSignals:[],team:[],metrics:{participants:0,active:0,new:0,matches:0,conversations:0}};
  await page.route('**/api/**',async route=>{
    const path=new URL(route.request().url()).pathname;
    if(path==='/api/session/')return route.fulfill({json:{authenticated:true,csrfToken:'export-token'}});
    if(path==='/api/bootstrap/')return route.fulfill({json:{navigation:'administration',role:'ADMIN'}});
    if(path==='/api/notifications/')return route.fulfill({json:{items:[],unread:0}});
    if(path==='/api/event-admin/support/')return route.fulfill({json:[]});
    if(path==='/api/event-admin/')return route.fulfill({json:data});
    if(path==='/api/event-admin/exports/'&&route.request().method()==='GET')return route.fulfill({body:'null',contentType:'application/json'});
    if(path==='/api/event-admin/exports/'&&route.request().method()==='POST') {
      requests++;assert.equal(route.request().headers()['x-csrftoken'],'export-token');
      return route.fulfill({json:pending});
    }
    if(path==='/api/event-admin/exports/export-1/') {
      polls++;
      return route.fulfill({json:completed?{...pending,state:'COMPLETED',progress:100,download:'/api/export.zip',term:'/api/term.pdf'}:{...pending,state:'PROCESSING',progress:35,stage:'Coletando dados'}});
    }
    throw Error('Unexpected request: '+path);
  });
  await page.goto(BASE_URL+'/#admin-more',{waitUntil:'networkidle'});
  await page.locator('.adm-bottom').getByRole('button',{name:'Mais',exact:true}).click();
  const control=page.locator('.event-export-control');
  await control.getByRole('button',{name:'Exportar dados',exact:true}).click();
  await control.getByRole('button',{name:/Aguardando Celery/}).waitFor();
  assert(await control.getByRole('button').isDisabled());
  await control.getByRole('button',{name:/35%/}).waitFor();
  completed=true;
  await control.getByRole('button',{name:'Baixar dados',exact:true}).click();
  const term=control.getByRole('link',{name:'Baixar o Termo',exact:true});
  const zip=control.getByRole('link',{name:'Baixar ZIP',exact:true});
  await term.waitFor();await zip.waitFor();
  assert.equal(await term.getAttribute('href'),'/api/term.pdf');
  assert.equal(await zip.getAttribute('href'),'/api/export.zip');
  assert.equal(await page.getByText('Exportação concluída.',{exact:true}).count(),0);
  assert.equal(requests,1);assert(polls>=2);assert.deepEqual(errors,[]);
  console.log('PASS: export request, disabled progress button, polling, completed dropdown and PDF/ZIP links.');
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
