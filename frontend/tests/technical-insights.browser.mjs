// Manual integration runner: production Next server + read-only real Technical API.
// All non-Technical Stock Detail APIs are disabled/scaffolded; no SSI acquisition.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdirSync} from 'node:fs';
const require=createRequire(import.meta.url);
const {chromium}=require(process.argv[2] || 'playwright');
const browser=await chromium.launch({headless:true,channel:process.argv[3] || 'chrome'});
const failures=[];
const realChecks=[];
mkdirSync('../data/technical_ui_validation',{recursive:true});
try {
 for(const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
  const context=await browser.newContext({viewport,locale:'en-GB'});
  await context.addInitScript(()=>localStorage.setItem('woofi.language.v1','en'));
  const page=await context.newPage();
  page.on('pageerror',error=>failures.push(error.message));
  await page.route('**/api/**',async route=>{
   const path=new URL(route.request().url()).pathname;
   if(path.startsWith('/api/technical/'))return route.continue();
   // Identity scaffold only, no market observations or fabricated financial data.
   if(path==='/api/stocks/FPT/overview')return route.fulfill({json:{stock:{id:1,symbol:'FPT',company_name:null,exchange:'HOSE'},history:[],market:{ticker:'FPT',as_of:null,close:null,source:'unavailable'},fundamentals:{period:null,source:'unavailable'},news:[]}});
   return route.fulfill({status:503,json:{detail:'Non-Technical source disabled in UI validation'}});
  });
  await page.goto('http://127.0.0.1:3011/stocks/FPT');
  const section=page.locator('#stock-technical-insights');
  await section.getByText('No meaningful technical change',{exact:true}).waitFor();
  assert.equal(await section.getByText('PROVISIONAL',{exact:true}).count(),1);
  assert.match(await section.innerText(),/8 Oct 2026/);
  assert.doesNotMatch(await section.innerText(),/VERIFIED/);
  const body=await (await context.request.get('http://127.0.0.1:3011/api/technical/FPT/daily/operational/latest')).json();
  assert.equal(body.kind,'provisional_packet');
  assert.equal(body.packet.ticker,'FPT');
  assert.equal(body.packet.packet_state,'NO_MEANINGFUL_TECHNICAL_CHANGE');
  assert.equal(body.packet.trading_session,'2026-10-08');
  realChecks.push({viewport,session:body.packet.trading_session,snapshot_id:body.snapshot_id,assurance:body.assurance});
  assert.equal(await section.evaluate(el=>el.scrollWidth<=el.clientWidth),true);
  await section.screenshot({path:'../data/technical_ui_validation/fpt-'+viewport.width+'.png'});
  // Synthetic transport cases exercise UI behavior only; do not alter stored data.
  let current=body, hold=null, started=null;
  await page.route('**/api/technical/**',async route=>{
   const captured=current, wait=hold;
   started?.();
   if(wait)await wait;
   try {await (captured===null?route.fulfill({status:503,json:{detail:'unavailable'}}):route.fulfill({json:captured}));}
   catch { /* An obsolete request may have been aborted by revalidation. */ }
  });
  const refresh=()=>page.evaluate(()=>window.dispatchEvent(new Event('focus')));
  const events=['one','two','three','four'].map(id=>({event_id:id,event_type:'unusual_volume',ticker:'FPT',trading_session:body.packet.trading_session,eligible:true,is_fixture:false,direction:'up',evidence:[{metric:'synthetic_test_only',value:123,unit:'shares'}],evidence_refs:['synthetic-ui-test']}));
  // A delayed obsolete result must not overwrite a newer completed request.
  current={...body,packet:{...body.packet,packet_state:'HAS_INSIGHTS',top_insights:events}};
  let release;
  hold=new Promise(resolve=>{release=resolve;});
  const requestStarted=new Promise(resolve=>{started=resolve;});
  await refresh();await requestStarted;
  await section.getByText('Loading Technical Insights…',{exact:true}).waitFor();
  assert.equal(await section.getByText('No meaningful technical change',{exact:true}).count(),0);
  hold=null;started=null;current=body;
  await refresh();await section.getByText('No meaningful technical change',{exact:true}).waitFor();
  release();await page.waitForTimeout(200);
  assert.equal(await section.locator('[data-insight]').count(),0);
  current={...body,packet:{...body.packet,packet_state:'HAS_INSIGHTS',top_insights:events}};
  await refresh();
  await section.locator('[data-insight="three"]').waitFor();
  assert.equal(await section.locator('[data-insight]').count(),3);
  await section.getByText('Inspect technical evidence').first().click();
  assert.match(await section.innerText(),/synthetic_test_only/);
  assert.equal(await section.evaluate(el=>el.scrollWidth<=el.clientWidth),true);
  current={kind:'diagnostic',ticker:'FPT',requested_session:body.packet.trading_session,readiness_status:'INCOMPLETE_EVIDENCE',reason_codes:['source_revision_detected'],safe_to_display_as_verified:false};
  await refresh();await section.getByText(/was withdrawn/).waitFor();
  assert.equal(await section.locator('[data-insight]').count(),0);
  current={...body,snapshot_id:'synthetic-corrected-version',snapshot_version:2,freshness:'STALE'};
  await refresh();await section.getByText('Source check overdue',{exact:false}).waitFor();
  await section.getByText(/Data provenance and checks/).click();
  assert.match(await section.innerText(),/Version 2/);
  current={kind:'diagnostic',ticker:'FPT',requested_session:null,readiness_status:'INCOMPLETE_EVIDENCE',reason_codes:['missing_calendar'],safe_to_display_as_verified:false};
  await refresh();await section.getByText(/not yet accepted/).waitFor();
  assert.equal(await section.getByText('PROVISIONAL',{exact:true}).count(),0);
  current=null;await refresh();await section.getByText(/temporarily unavailable/).waitFor();
  assert.equal(await section.getByText('No meaningful technical change',{exact:true}).count(),0);
  current=body;
  await section.getByRole('button',{name:'Retry',exact:true}).click();
  await section.getByText('No meaningful technical change',{exact:true}).waitFor();
  await context.close();
 }
 assert.deepEqual(failures,[]);
 console.log(JSON.stringify({status:'PASS',realChecks,syntheticStates:['loading','obsolete-response','multiple','retracted','corrected-v2','stale','missing-calendar','API-error','retry'],pageErrors:failures}));
} finally {await browser.close();}
