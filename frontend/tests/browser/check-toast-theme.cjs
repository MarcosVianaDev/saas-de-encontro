const { BASE_URL, MOCK_URL, launch, testCredentials, mockSync } = require('./helpers.cjs');
const {chromium}=require('playwright');const assert=require('assert/strict');
(async()=>{const browser=await launch();try{
const context=await browser.newContext({viewport:{width:390,height:844},colorScheme:'light'});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
const data={navigation:'participant',onboardingComplete:true,active:true,profile:{first:'Pessoa',last:'Teste',month:'1',year:'1990',gender:'Mulheres',bio:'Uma descrição de perfil com mais de cinquenta caracteres para completar o cadastro.',interests:[],purpose:''},photos:[],filters:{min:18,max:35,gender:'Todos',interests:[],purpose:''},people:[],discovery:[],chats:{},chatStates:{},seen:[],liked:[],saved:[],event:{id:'test',name:'Evento',state:'RUNNING',mode:'ONLINE'}};
await page.route('**/api/**',async route=>{let body={};const path=new URL(route.request().url()).pathname;if(path==='/api/session/')body={authenticated:true,csrfToken:'test'};else if(path==='/api/bootstrap/')body=data;else if(path==='/api/sync/')body=mockSync(data);else if(path==='/api/catalog/')body={people:data.people,discovery:data.discovery};else if(path==='/api/notifications/')body={items:[{id:'theme-test',title:'Aviso do evento',body:'Mensagem de teste',kind:'announcement',read:false,created:new Date().toISOString(),action:''}],unread:1};else if(path==='/api/health/')body={status:'ok'};else if(path==='/api/support/')body=[];await route.fulfill({json:body});});
await page.goto(BASE_URL + '/#mensagens');await page.locator('.notification-toast').waitFor();
const choose=async label=>{const mode=label===String.fromCharCode(67,108,97,114,111)?'light':label===String.fromCharCode(69,115,99,117,114,111)?'dark':'auto';await page.evaluate(async mode=>(await import('/theme.ts')).setThemeMode(mode),mode);};
const colors=()=>page.locator('.notification-toast').evaluate(el=>({background:getComputedStyle(el).backgroundColor,header:getComputedStyle(el.querySelector('.toast-header')).backgroundColor,border:getComputedStyle(el).borderTopColor}));
await choose('Escuro');
assert.deepEqual(await colors(),{background:'rgb(25, 30, 44)',header:'rgb(32, 38, 56)',border:'rgb(57, 65, 87)'});
await choose('Claro');assert.equal((await colors()).background,'rgba(255, 255, 255, 0.97)');
await page.emulateMedia({colorScheme:'dark'});await choose('Automático');await page.waitForFunction(()=>document.documentElement.dataset.bsTheme==='dark');
assert.equal((await colors()).background,'rgb(25, 30, 44)');
assert.deepEqual(errors,[]);console.log('PASS: notification pop-up background, header and border follow dark, light and automatic themes');
await context.close();
}finally{await browser.close();}})().catch(e=>{console.error(e.message);process.exit(1)});
