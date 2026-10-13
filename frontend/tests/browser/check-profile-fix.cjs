const { BASE_URL, MOCK_URL, launch, testCredentials } = require('./helpers.cjs');
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const assert = require('assert/strict');
(async()=>{
const session = execFileSync('docker',(process.env.TEST_BACKEND_CONTAINER ? ['exec','-i',process.env.TEST_BACKEND_CONTAINER] : ['compose','exec','-T','backend']).concat(['python','manage.py','shell','-c',"import json; from django.contrib.sessions.backends.db import SessionStore; from apps.participants.models import EventParticipant; from demo.data import demo_id; p=EventParticipant.objects.get(pk=demo_id('actor')); s=SessionStore(); s['_auth_user_id']=str(p.user_id); s['_auth_user_backend']='django.contrib.auth.backends.ModelBackend'; s['_auth_user_hash']=p.user.get_session_auth_hash(); s['event_id']=str(p.event_id); s['navigation']='participant'; s.save(); print(json.dumps({'cookie':s.session_key}))"]),{encoding:'utf8'}).trim().split('\n').at(-1);
const browser=await launch();
try{
for(const legacy of [false,true]){
const context=await browser.newContext();
await context.addCookies([{name:'sessionid',value:JSON.parse(session).cookie,url:BASE_URL}]);
const page=await context.newPage(); const errors=[];
page.on('pageerror',e=>errors.push(e.message));
if(legacy) await page.route('**/api/bootstrap/',async route=>{
 const res=await route.fetch(); const data=await res.json();
 delete data.profile.interests; delete data.profile.purpose;
 await route.fulfill({response:res,json:data});
});
await page.goto(BASE_URL + '/#perfil');
await page.locator('#profile-form').waitFor().catch(async error=>{console.log('Profile diagnostics',legacy,errors,await page.locator('body').innerText());throw error;});
const data=await page.evaluate(async()=>(await fetch('/api/profile/')).json());
console.log('API_PROFILE_FIELDS',Object.keys(data.profile));
const interests=page.locator('#profile-form fieldset').filter({has:page.locator('legend').filter({hasText:'Interesses'})});
await interests.getByRole('button',{name:'Tecnologia',exact:true}).click();
await interests.getByRole('button',{name:'Tecnologia',exact:true}).click();
await page.locator('#profile-form').getByRole('button',{name:'Amizade',exact:true}).click();
assert.deepEqual(errors,[]);
console.log('PASS',legacy?'legacy payload renders and options work':'live participant profile renders and options work');
await context.close();
}
}finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exit(1)});

