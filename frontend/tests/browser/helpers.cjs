const { chromium } = require('playwright');
const fs = require('node:fs');
const BASE_URL = process.env.TEST_BASE_URL || 'http://localhost:8080';
const MOCK_URL = process.env.TEST_MOCK_URL || 'http://localhost:5174';
const credentials = () => JSON.parse(fs.readFileSync(process.env.TEST_CREDENTIALS_FILE || '.tools/demo-credentials.json', 'utf8'));
const launch = () => chromium.launch({headless: true, ...(process.env.TEST_BROWSER_PATH ? {executablePath:process.env.TEST_BROWSER_PATH} : process.platform==='win32' ? {channel:'msedge'} : {})});
const mockSync = data => ({
  cursor: 'mock-sync', hasMore: false, messages: [], peers: [], blocked: [],
  status: { active: data.active, onboardingComplete: data.onboardingComplete,
    socialAvailable: data.socialAvailable ?? (data.active && data.event.state === 'RUNNING'), event: data.event },
  chatStates: data.chatStates || {}, unread: Object.keys(data.chats || {}).filter(peer => data.chats[peer].some(message => message.unread)),
});
async function api(page,path,method='GET',body) {
  return page.evaluate(async({path,method,body})=>{
    const client = await import('/backend-client.ts');
    await client.api.session();
    return client.request(path, method, body);
  },{path,method,body});
}
async function login(page,email) {
  await page.goto(BASE_URL,{waitUntil:'networkidle'});
  await page.getByLabel('E-mail',{exact:true}).fill(email);
  await page.getByLabel('Senha',{exact:true}).fill(credentials().password);
  await page.locator('form').getByRole('button',{name:/Entrar/}).click();
  await page.waitForFunction(()=>!document.querySelector('.login-screen'));
  if(await page.getByRole('heading',{name:'Onde você deseja entrar?'}).isVisible()) {
    await page.locator('section').filter({has:page.getByRole('heading',{name:'Conecta São Paulo',exact:true})}).getByRole('button',{name:'Participar',exact:true}).click();
  }
  await page.locator(email===credentials().email ? '.bottom-nav' : '.global-administration').waitFor();
}
async function selectEvent(page) {
  await page.locator('.global-administration').waitFor();
  await page.locator('.adm-bottom').getByRole('button',{name:'Eventos',exact:true}).click();
  const card=page.locator('section').filter({has:page.getByRole('heading',{name:'Conecta São Paulo',exact:true})}).last();
  await card.getByRole('button',{name:'Administrar evento',exact:true}).click();
  await page.locator('.adm-hero').waitFor();
}
module.exports={BASE_URL,MOCK_URL,launch,testCredentials:credentials,login,api,selectEvent,mockSync};
