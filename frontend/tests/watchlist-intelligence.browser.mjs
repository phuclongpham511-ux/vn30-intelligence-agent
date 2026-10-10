// Production Next + isolated tests/watchlist_ui_server.py. Mutations are test
// transport fixtures only; never stored as investor evidence.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdirSync,writeFileSync} from 'node:fs';
const require=createRequire(import.meta.url);
const {chromium}=require(process.argv[2]||'playwright');
const browser=await chromium.launch({headless:true,channel:'chrome'});
const origin='http://127.0.0.1:3012',output='../data/watchlist_ui_validation';
mkdirSync(output,{recursive:true});
const results=[],errors=[],copy=value=>JSON.parse(JSON.stringify(value));
try {
 for(const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
  const context=await browser.newContext({viewport,locale:'en-GB'});
  await context.addInitScript(()=>{localStorage.setItem('woofi.language.v1','en');if(!localStorage.getItem('vn30.watchlist.v1'))localStorage.setItem('vn30.watchlist.v1',JSON.stringify({symbols:[],seen:{},communitySeen:{}}));});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  const calls=[];let current=null,override=false,hold=null,started=null;
  await page.route('**/api/**',async route=>{
   const path=new URL(route.request().url()).pathname;calls.push(path);
   if(path==='/api/watchlists/intelligence') {
    if(!override)return route.continue();
    const captured=copy(current),wait=hold;started?.();if(wait)await wait;
    try{return captured===null?await route.fulfill({status:503,json:{detail:'Synthetic failure'}}):await route.fulfill({json:captured});}catch{return;}
   }
   if(path==='/api/stocks/universe') {
    const size=Number(new URL(route.request().url()).searchParams.get('limit'));assert.ok(size<=8,'no full universe');
    return route.fulfill({json:{items:[{symbol:'XYZ',exchange:'HOSE',company_name:'Synthetic browser test issuer',display_name_en:'Synthetic browser test issuer'}],total:1,total_universe:1,offset:0,limit:size,status:'healthy'}});
   }
   return route.fulfill({status:503,json:{detail:'Unrelated source disabled in validation'}});
  });
  await page.goto(origin+'/watchlist');await page.getByText('No stocks followed yet',{exact:true}).waitFor();
  assert.equal(calls.filter(c=>c==='/api/watchlists/intelligence').length,0);
  await page.getByRole('combobox',{name:'Stock to follow',exact:true}).fill('XYZ');
  await page.getByRole('listbox',{name:'Stock to follow results',exact:true}).getByRole('option').first().click();await page.getByRole('button',{name:'Follow XYZ',exact:true}).click();
  const section=page.getByRole('article',{name:'XYZ monitoring',exact:true});
  await section.getByText('XYZ reports synthetic browser test results',{exact:true}).waitFor();
  await section.getByText('Synthetic browser test issuer',{exact:true}).waitFor();
  await section.getByText('PROVISIONAL',{exact:true}).waitFor();
  const response=await context.request.post(origin+'/api/watchlists/intelligence',{data:{symbols:['XYZ'],offset:0,page_size:12}});
  assert.equal(response.status(),200);assert.equal(response.headers()['cache-control'],'no-store');
  const base=await response.json();assert.equal(base.stocks[0].news.items.length,1);assert.equal(base.stocks[0].community.items.length,1);
  const storage=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('vn30.watchlist.v1')));
  assert.equal((await storage()).reviewedAt,undefined);
  await section.getByText('View source evidence',{exact:true}).first().click();assert.equal((await storage()).reviewedAt,undefined);
  for(const kind of ['News','Community','Technical updates'])await section.getByRole('button',{name:'Mark displayed '+kind+' reviewed',exact:true}).click();
  await section.getByText('No unreviewed items on this page',{exact:true}).waitFor();
  const receipt=await storage();assert.ok(receipt.reviewedAt.XYZ);
  await page.reload();await section.getByText('No unreviewed items on this page',{exact:true}).waitFor();assert.deepEqual((await storage()).receipts,receipt.receipts);
  const refresh=()=>page.evaluate(()=>window.dispatchEvent(new Event('focus')));
  override=true;current=copy(base);
  const story=current.stocks[0].news.items[0],articleId=Object.keys(story.revision_members)[0];
  story.revision_members[articleId]='synthetic-correction';story.title='XYZ reports corrected synthetic browser results';
  await refresh();await section.getByText('Updated since review',{exact:true}).waitFor();
  await section.getByRole('button',{name:'Mark displayed News reviewed',exact:true}).click();
  current.stocks[0].news.items.push({...copy(story),id:'news:synthetic-new',entity_id:'synthetic-new',revision:'new',title:'XYZ announces synthetic new story',revision_members:{new:'new'}});
  await refresh();await section.getByText('XYZ announces synthetic new story',{exact:true}).waitFor();assert.equal(await section.getByText('Unreviewed',{exact:true}).count(),1);
  current.stocks[0].technical={items:[],has_more:false,truncated:false,data:{kind:'diagnostic',ticker:'XYZ',requested_session:base.stocks[0].technical.data.packet.trading_session,readiness_status:'INCOMPLETE_EVIDENCE',reason_codes:['source_revision_detected'],safe_to_display_as_verified:false}};
  await refresh();await section.getByText(/was withdrawn/).waitFor();assert.equal(await section.getByText('PROVISIONAL',{exact:true}).count(),0);assert.equal(await section.locator('[data-insight]').count(),0);
  await section.getByText('Technical updates · Count unavailable',{exact:true}).waitFor();
  current.stocks[0].technical.waiting_for_gate=true;current.stocks[0].technical.next_check_due_at='2026-10-11T01:00:00Z';
  await refresh();await section.getByText('Technical data pending the delayed EOD gate',{exact:true}).waitFor();
  current.stocks[0].technical.waiting_for_gate=false;current.stocks[0].technical.awaiting_source_check=true;
  await refresh();await section.getByText('Delayed EOD gate elapsed; awaiting source check',{exact:true}).waitFor();
  current.stocks[0].technical=copy(base.stocks[0].technical);current.stocks[0].technical.items=[];current.stocks[0].technical.data.packet.top_insights=[];
  current.stocks[0].technical.data.packet.packet_state='NO_MEANINGFUL_TECHNICAL_CHANGE';
  await refresh();await section.getByText('No meaningful technical change',{exact:true}).waitFor();
  current.stocks[0].technical.data.packet.packet_state='TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE';
  await refresh();await section.getByText('Technical evidence is incomplete; insights are withheld.',{exact:true}).waitFor();await section.getByText('Technical updates · Count unavailable',{exact:true}).waitFor();
  let release;hold=new Promise(resolve=>{release=resolve;});const began=new Promise(resolve=>{started=resolve;});await refresh();await began;
  hold=null;started=null;current=copy(base);await refresh();await section.getByText('PROVISIONAL',{exact:true}).waitFor();release();await page.waitForTimeout(150);assert.equal(await section.getByText('PROVISIONAL',{exact:true}).count(),1);
  current=null;await refresh();await page.getByText('Watchlist updates are temporarily unavailable. Counts are unknown.',{exact:false}).waitFor();assert.equal(await section.locator('[data-update]').count(),0);
  current=copy(base);await page.getByRole('button',{name:'Retry updates',exact:true}).click();await section.getByText('XYZ reports synthetic browser test results',{exact:true}).waitFor();
  current.stocks[0].community.items=Array.from({length:12},(_,n)=>({...copy(base.stocks[0].community.items[0]),id:'community:page-'+n,entity_id:'page-'+n,revision:'page-v1',title:'Synthetic paged discussion '+n}));current.stocks[0].community.has_more=true;
  await refresh();await section.getByText('Community · 12 unreviewed on this page',{exact:true}).waitFor();await section.getByRole('button',{name:'Mark displayed Community reviewed',exact:true}).click();await section.getByText('Community · 9 unreviewed on this page',{exact:true}).waitFor();
  await section.getByRole('button',{name:'Show all 12 loaded updates',exact:true}).click();assert.equal(await section.locator('[data-update^="community:"]').count(),12);
  current={...copy(base),offset:12};current.stocks[0].news.items=[];current.stocks[0].community.items=[];
  await page.getByRole('button',{name:'Next page',exact:true}).click();await page.getByText('Page 2 · up to 12 items per source and stock',{exact:true}).first().waitFor();await section.getByText('Community · 0 unreviewed on this page',{exact:true}).waitFor();
  current=copy(base);await page.getByRole('button',{name:'Previous page',exact:true}).click();await section.getByText('XYZ reports synthetic browser test results',{exact:true}).waitFor();
  assert.equal(await section.getByRole('link',{name:'Open XYZ stock detail',exact:true}).getAttribute('href'),'/stocks/XYZ');assert.match(await section.getByRole('link',{name:'News mentioning XYZ',exact:true}).getAttribute('href'),/ticker=XYZ/);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:output+'/watchlist-'+viewport.width+'-dark.png',fullPage:true});
  await page.getByRole('button',{name:'Switch to light mode',exact:true}).click();
  await page.waitForFunction(()=>document.documentElement.classList.contains('light'));
  await page.screenshot({path:output+'/watchlist-'+viewport.width+'-light.png',fullPage:true});
  await page.evaluate(()=>{localStorage.setItem('woofi.language.v1','vi');window.dispatchEvent(new StorageEvent('storage',{key:'woofi.language.v1'}));});
  await page.getByRole('heading',{name:'Danh sách theo dõi',exact:true}).waitFor();await page.screenshot({path:output+'/watchlist-'+viewport.width+'-vi.png',fullPage:true});
  // Multiple watched identities and unavailable metadata never become no-change.
  override=false;
  await page.evaluate(()=>{localStorage.setItem('woofi.language.v1','en');localStorage.setItem('vn30.watchlist.v1',JSON.stringify({symbols:['XYZ','EMPTY','MISSING'],seen:{},communitySeen:{}}));window.dispatchEvent(new StorageEvent('storage',{key:'woofi.language.v1'}));window.dispatchEvent(new StorageEvent('storage',{key:'vn30.watchlist.v1'}));});
  await page.getByRole('article',{name:'MISSING monitoring',exact:true}).getByText('Stock data is unavailable. This is not a no-change result.',{exact:true}).waitFor();
  await page.getByRole('article',{name:'EMPTY monitoring',exact:true}).getByText('Technical evidence is not yet accepted for this ticker.',{exact:true}).waitFor();
  assert.equal(await page.locator('#watchlist-technical-XYZ').count(),1);
  assert.equal(await page.locator('#watchlist-technical-EMPTY').count(),1);
  await page.evaluate(()=>{localStorage.setItem('vn30.watchlist.v1','{broken');window.dispatchEvent(new StorageEvent('storage',{key:'vn30.watchlist.v1'}));});
  await page.getByText('Browser storage is unavailable or saved data cannot be read. Your saved Watchlist has not been overwritten. Reload to retry.',{exact:true}).waitFor();
  await page.getByText('Review state unavailable. Unread counts are unknown.',{exact:true}).first().waitFor();
  assert.equal(await page.evaluate(()=>localStorage.getItem('vn30.watchlist.v1')),'{broken');
  results.push({viewport,realProxy:true,realDatabase:true,overflow:false,states:['empty','follow','news','community','technical','explicit-review','reload','revision','new-arrival','retraction','pending-gate','gate-elapsed','no-change','incomplete','obsolete-response','error','retry','partial-review','pagination','Vietnamese','light','multiple-stocks','unknown-stock','corrupt-storage']});
  await context.close();
 }
 assert.deepEqual(errors,[]);const report={status:'PASS',results,pageErrors:errors};writeFileSync(output+'/report.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
} finally {await browser.close();}
