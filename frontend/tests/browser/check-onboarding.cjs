const { BASE_URL, MOCK_URL, launch, testCredentials } = require('./helpers.cjs');
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const crypto=require('node:crypto');
(async()=>{
  const credentials=testCredentials();
  const browser=await launch();
  const errors=[];let lastPage;
  const base=BASE_URL;
  const photo='frontend/public/images/photo-1544005313-94ddf0286df2.jpg';
  const photos=[photo,'frontend/public/images/photo-1535713875002-d1d0cf377fde.jpg','frontend/public/images/photo-1534528741775-53994a69daeb.jpg'];
  async function page(){const context=await browser.newContext({viewport:{width:390,height:844}});const p=await context.newPage();lastPage=p;p.on('pageerror',e=>errors.push(e.message));await p.goto(base,{waitUntil:'networkidle'});return p;}
  async function api(p,path,method='GET',body){return p.evaluate(async({path,method,body})=>{const s=await(await fetch('/api/session/')).json();const r=await fetch(`/api/${path}`,{method,headers:{'Content-Type':'application/json','X-CSRFToken':s.csrfToken},body:body?JSON.stringify(body):undefined});if(!r.ok)throw Error(`${path}: HTTP ${r.status}`);return r.json();},{path,method,body});}
  try{
    const root=await page();
    await api(root,'auth/login/','POST',{email:credentials.adminEmail,password:credentials.password});
    const tag=crypto.randomUUID();
    const client=await api(root,'global/','POST',{action:'create_client',contact:'Validação fictícia',email:`client-${tag}@example.invalid`,phone:'11999990000'});
    await api(root,'global/','POST',{action:'update_client',id:client.id,contact:'Validação fictícia',email:`client-${tag}@example.invalid`,phone:'11999990000',organization:`Onboarding fictício ${tag}`});
    const created=await api(root,'global/','POST',{action:'create_event',client:client.id,event:'Onboarding fictício — validação do MVP',mode:'PHYSICAL',latitude:'-23.550000',longitude:'-46.630000',starts:new Date(Date.now()+3600000).toISOString(),ends:new Date(Date.now()+14400000).toISOString(),responsible:`client-${tag}@example.invalid`});
    const event=created.id;
    await api(root,'global/event/','POST',{event});
    await api(root,'event-admin/passes/','POST',{action:'offer',name:'Duas revelações fictícias',price:'0',limit:2,minutes:0});
    await api(root,'event-admin/configuration/','PUT',{starts_at:new Date(Date.now()-3600000).toISOString(),confirmed:true});
    await api(root,'event-admin/transition/','POST',{state:'OPEN'});
    await api(root,'event-admin/transition/','POST',{state:'RUNNING'});
    const admin=await api(root,'event-admin/');const invite=new URL(admin.event.joinPath,base).searchParams.get('invite');
    const password=`Fixture!${crypto.randomBytes(12).toString('hex')}`;
    const participants=[];
    for(const suffix of ['A','B']){
      const p=await page();const email=`validation-${tag}-${suffix}@example.invalid`;
      const result=await api(p,'auth/register/','POST',{email,password,invite});
      await p.reload({waitUntil:'networkidle'});
      await p.getByRole('heading',{name:'Seu perfil',exact:true}).waitFor();
      await p.getByLabel('Nome',{exact:true}).fill(`Pessoa fictícia ${suffix}`);
      await p.getByLabel('Sobrenome',{exact:true}).fill('Validação');
      await p.getByLabel('Mês de nascimento').selectOption('5');await p.getByLabel('Ano de nascimento').selectOption('1996');
      await p.getByLabel('Sobre você').fill('Perfil fictício criado para verificar o cadastro, as fotos e a ativação do MVP.');
      await p.getByRole('button',{name:'Continuar',exact:true}).click();
      await p.getByLabel('Adicionar fotos').setInputFiles(photos);
      await p.waitForFunction(()=>document.querySelectorAll('.onboarding-photos img').length===3);
      await p.getByRole('button',{name:'Enviar para ativação',exact:true}).click();
      await p.locator('.app-screen').waitFor();
      const state=await api(p,'bootstrap/');assert(state.onboardingComplete);assert.equal(state.registrationStatus,'PENDING');assert.equal(state.photos.length,3);
      participants.push({page:p,id:state.event.id,email,name:`Pessoa fictícia ${suffix}`});
      console.log(`Onboarding fictício ${suffix}: two steps and three authenticated photos validated.`);
    }
    const operator=await page();const operatorEmail=`validation-${tag}-operator@example.invalid`;
    await api(operator,'auth/register/','POST',{email:operatorEmail,password,invite});
    await api(root,'event-admin/team/','POST',{email:operatorEmail,role:'OPERATOR',permissions:['passes'],active:true});
    await api(operator,'contexts/','POST',{key:`administration:${event}`});
    await operator.reload({waitUntil:'networkidle'});
    await operator.locator('.adm-workspace').waitFor();
    await operator.locator('.adm-bottom').getByRole('button',{name:'Participantes',exact:true}).click();
    for(const person of participants){
      await api(person.page,'location/','POST',{latitude:'-23.550000',longitude:'-46.630000',accuracy:10});
      await operator.locator('.adm-person').filter({hasText:person.name}).click();
      await operator.locator('input[type=file]').setInputFiles(photo);
      await operator.getByRole('button',{name:'Usar esta foto',exact:true}).click();
      await operator.getByText('Operação registrada.',{exact:true}).waitFor();
      await operator.getByRole('button',{name:'Ativar perfil',exact:true}).click();
      await operator.getByRole('button',{name:/Voltar aos participantes/}).click();
      const state=await api(person.page,'bootstrap/');assert.equal(state.active,true);assert(state.activated);
    }
    const a=participants[0].page,b=participants[1].page;
    const active=await api(a,'bootstrap/');const peer=active.people.find(p=>p.name===participants[1].name);
    const other=await api(b,'bootstrap/');const actor=other.people.find(p=>p.name===participants[0].name);
    await api(b,`interactions/${actor.id}/`,'POST',{decision:'LIKE'});
    const locked=await api(a,'likes-received/');assert.equal(locked.hidden,1);assert.deepEqual(locked.people,[]);
    const passData=await api(operator,'event-admin/passes/');
    await api(operator,'event-admin/passes/','POST',{participant:actor.id,offer:passData.offers[0].id,origin:'Validação fictícia de balcão'});
    const revealed=await api(a,'likes-received/');assert.equal(revealed.hidden,0);assert.equal(revealed.people[0].id,peer.id);
    await api(a,'likes-received/');
    const issued=(await api(operator,'event-admin/passes/')).passes.find(p=>p.participant===actor.id);
    assert(issued);assert.equal(issued.used,1);assert.equal(issued.limit,2);
    const match=await api(a,`interactions/${peer.id}/`,'POST',{decision:'LIKE'});assert(match.match);
    const detail=await api(a,`participants/${peer.id}/`);assert(detail.outfit);assert.equal((await a.request.get(base+detail.outfit)).status(),200);
    await api(a,`conversations/${peer.id}/messages/`,'POST',{text:'Mensagem fictícia para validar a conversa após o match.'});
    await a.reload({waitUntil:'networkidle'});
    await a.evaluate(()=>location.hash='mensagens');
    await a.locator('.conversation-row').filter({hasText:participants[1].name}).click();
    await a.getByText('Mensagem fictícia para validar a conversa após o match.',{exact:true}).waitFor();
    await a.screenshot({path:'.tools/ui-check/screenshots/mvp-onboarding-match-mobile.png'});
    const result=await api(a,'bootstrap/');assert(result.activated);assert(result.onboardingComplete);
    assert.deepEqual(errors,[]);
    console.log('PASS: new-event onboarding, three photos, operator outfit capture and activation, protected received like, authorized pass grant/reveal, match, private outfit and persisted conversation.');
  }catch(e){if(lastPage&&!lastPage.isClosed()){await lastPage.screenshot({path:'.tools/ui-check/screenshots/mvp-onboarding-error.png'});console.log('Failure route:',new URL(lastPage.url()).hash);}throw e;}finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exit(1);});
