const {BASE_URL,MOCK_URL,launch}=require('./helpers.cjs');
const assert=require('node:assert/strict');
(async()=>{
const browser=await launch();
try {
  const page=await browser.newPage();const errors=[];let sessionCalls=0,unavailable=true;
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/api/session/',route=>{
    sessionCalls++;
    return route.fulfill(unavailable?{status:503,json:{detail:'Backend indisponível para teste.'}}:{json:{authenticated:false,csrfToken:'mode-token'}});
  });
  await page.goto(BASE_URL,{waitUntil:'networkidle'});
  await page.getByRole('status').filter({hasText:'Backend indisponível para teste.'}).waitFor();
  assert(sessionCalls>0);
  assert.equal(await page.locator('.participant-tile,.discovery-card,.conversation-row').count(),0);
  unavailable=false;
  await page.reload({waitUntil:'networkidle'});
  await page.getByLabel('E-mail',{exact:true}).waitFor();
  assert(sessionCalls>=2);
  assert.equal(await page.locator('.participant-tile,.discovery-card,.conversation-row').count(),0);
  const mock=await browser.newPage();let apiCalls=0;
  mock.on('request',r=>{if(new URL(r.url()).pathname.startsWith('/api/'))apiCalls++;});
  await mock.goto(MOCK_URL+'/#participantes',{waitUntil:'networkidle'});
  assert.equal(await mock.locator('.participant-tile').count(),50);
  assert.equal(apiCalls,0);assert.deepEqual(errors,[]);
  console.log('PASS: Django session failure stays visible without mock fallback, recovery on reload, mock has no API calls.');
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
