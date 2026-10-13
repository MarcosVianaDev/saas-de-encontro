const { BASE_URL, MOCK_URL, launch, testCredentials } = require('./helpers.cjs');
const {chromium}=require('playwright'); const assert=require('assert/strict');
(async()=>{const browser=await launch();
try{for(const required of [false,true]){
const context=await browser.newContext();const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
let saved=0;
const data={navigation:'participant',onboardingComplete:false,active:false,profile:{first:'Pessoa',last:'Teste',month:'1',year:'1990',gender:'Mulheres',bio:'Uma descrição de perfil com mais de cinquenta caracteres para validar o cadastro inicial.',interests:[],purpose:''},photos:['/images/profile-placeholder.svg','/images/profile-placeholder.svg','/images/profile-placeholder.svg'],filters:{min:18,max:35,gender:'Todos',interests:[],purpose:''},people:[],discovery:[],chats:{},chatStates:{},seen:[],liked:[],saved:[],profileTopics:[{id:'optional',key:'optional',name:'Opcional',options:['Outro'],multiple:true,required:false},...(required?[{id:'required',key:'required',name:'Obrigatório',options:['Escolha'],multiple:true,required:true,minimum:1}]:[])],profileFields:[],event:{id:'test',name:'Evento Teste',mode:'ONLINE',state:'OPEN'}};
await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;let body={};if(path==='/api/session/')body={authenticated:true,csrfToken:'test'};else if(path==='/api/bootstrap/')body=data;else if(path==='/api/profile/'&&route.request().method()==='PUT'){saved++;body={...data,onboardingComplete:true};}else if(path==='/api/notifications/')body={items:[],unread:0};else if(path==='/api/health/')body={status:'ok'};else if(path==='/api/support/')body=[];await route.fulfill({json:body});});
await page.goto(BASE_URL + '/#perfil');await page.locator('.participant-onboarding').waitFor();
assert.equal(await page.locator('.participant-onboarding fieldset').count(),0);
await page.getByRole('button',{name:'Continuar',exact:true}).click();
await page.getByRole('heading',{name:'Suas fotos',exact:true}).waitFor();
assert.equal(await page.locator('.participant-onboarding fieldset').count(),0);
if(required){await page.getByRole('button',{name:'Continuar',exact:true}).click();await page.getByRole('heading',{name:'Requisitos do evento',exact:true}).waitFor();assert.equal(await page.getByText('Opcional',{exact:true}).count(),0);await page.getByRole('button',{name:'Enviar para ativação',exact:true}).click();await page.getByRole('alert').waitFor();assert.equal(saved,0);await page.getByRole('button',{name:'Escolha',exact:true}).click();}
else assert.equal(await page.getByRole('heading',{name:'Requisitos do evento',exact:true}).count(),0);
await page.getByRole('button',{name:'Enviar para ativação',exact:true}).click();await page.locator('.participant-onboarding').waitFor({state:'hidden'});assert.equal(saved,1);assert.deepEqual(errors,[]);console.log('PASS',required?'required topics in third step and enforced before save':'optional topics omitted and two-step registration');await context.close();
}}finally{await browser.close();}})().catch(e=>{console.error(e.message);process.exit(1)});
