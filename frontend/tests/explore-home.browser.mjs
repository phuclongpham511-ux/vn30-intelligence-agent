// Run against a production Next server. All API fixtures are synthetic UI evidence;
// no upstream acquisition, credentials, stored market data or other worktrees are used.
// node tests/explore-home.browser.mjs <playwright-module-path> [base-url]
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdirSync,writeFileSync} from 'node:fs';
const require=createRequire(import.meta.url);
const {chromium}=require(process.argv[2]||'playwright');
const {expect}=require(process.argv[2]?process.argv[2]+'/test':'playwright/test');
const base=process.argv[3]||'http://127.0.0.1:3012';
const out='../data/explore_home_v2';
mkdirSync(out,{recursive:true});
const browser=await chromium.launch({headless:true,channel:'chrome'});
const checks=[],pageErrors=[];
const now=new Date().toISOString();
const day=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const securities=Array.from({length:32},(_,n)=>({symbol:`T${String(n).padStart(2,'0')}`,exchange:['HOSE','HNX','UPCOM'][n%3],display_name_en:`Synthetic issuer ${n}`,company_name:`Doanh nghiệp thử nghiệm ${n}`}));
const groups={groups:{VN30:securities.slice(0,12).map(row=>row.symbol),VN100:securities.map(row=>row.symbol)},status:'healthy',source:'SSI:FastConnect',last_synced_at:now};
const story=n=>{
 const article={id:`article-${n}`,story_id:`story-${n}`,title:`Synthetic market story ${n}`,url:`https://example.org/story-${n}`,source_name:'Fixture publisher',source_id:'fixture',publisher_group:'fixture',published_at:now,first_seen_at:now,last_seen_at:now,thumbnail_url:`${base}/__ui_fixture/photo.svg`,tickers:[],topics:[],sectors:[],is_fixture:true};
 return {story:{id:`story-${n}`,source_count:2,article_count:2,representative_title:article.title},representative_article:article,articles:[article],research_category:['COMPANY','INDUSTRY','MARKET_BRIEF'][n%3]};
};
const stories=[story(0),story(0),story(1),story(2)];
const communityItem={id:'discussion',revision_id:'test-revision',source_id:'f319_public',source_item_id:'test-only',item_type:'comment',title:'Synthetic discussion title',excerpt:'Synthetic excerpt about Vietnamese equity research.',url:'https://newf319.com/threads/synthetic-ui-test.1/',author:null,published_at:now,last_seen_at:now,tickers:['T01'],replies:null,views:null,is_fixture:true};
const source={source_id:'f319_public',name:'F319',enabled:true,url:'https://newf319.com/',qualification:'test fixture',status:'stale',poll_interval_minutes:15,last_attempt_at:now,last_success_at:now,last_error:null,items_received:1};
const pulse={as_of:now,sampled_items:1,unique_items:1,truncated:false,coverage_partial:true,window:{kind:'today',label:'Today',timezone:'Asia/Ho_Chi_Minh',start:now,end:now},sources:[source],items:[communityItem],active_tickers:[{ticker:'T01',item_count:1}],themes:[{id:'theme',label:'Synthetic discussion theme',keywords:['research'],summary:communityItem.excerpt,summary_kind:'extractive',item_count:1,source_count:1,source_ids:['f319_public'],latest_at:now,representative_id:'discussion',evidence_ids:['discussion']}]};
const freshIndex={status:'fresh',session:'closed',as_of:now,snapshot:{index:'VNINDEX',level:1234.56,change:5.67,change_percent:0.46,total_volume:null,total_value:null,trading_date:day,updated_at:now,fetched_at:now,source:'Synthetic test fixture',session:'closed'}};
try {
 for(const viewport of [{width:1440,height:1000},{width:390,height:844}]){
  const context=await browser.newContext({viewport,locale:'en-GB'});
  await context.addInitScript(()=>localStorage.setItem('woofi.language.v1','en'));
  const page=await context.newPage();page.setDefaultTimeout(10000);page.on('pageerror',error=>pageErrors.push(error.message));
  const requests=[];
  let failUniverse=false,failHot=false,failCommunity=false,failSearch=false,failImage=false,emptyUniverse=false,emptyHot=false,emptyCommunity=false,indexMode='fresh';
  let releaseInitial;
  let initialHold=new Promise(resolve=>{releaseInitial=resolve;});
  let delayedQuery=null,queryStarted=null,queryHold=null;
  await page.route('**/__ui_fixture/photo.svg',route=>failImage?route.fulfill({status:404,body:''}):route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="160" height="120"><rect width="160" height="120" fill="#517990"/><text x="12" y="65" fill="white" font-size="16">Test source image</text></svg>'}));
  await page.route('**/api/**',async route=>{
   const url=new URL(route.request().url()),path=url.pathname,q=url.searchParams;
   requests.push({path,query:url.search});
   const json=value=>route.fulfill({json:value});
   const error=()=>route.fulfill({status:503,json:{detail:'Synthetic test failure'}});
   if(path==='/api/ingestion/refresh'||path==='/api/stocks/live-release')return json({status:'test-only'});
   if(path==='/api/stocks/universe'){
    const text=q.get('q')||'',size=Number(q.get('limit')),offset=Number(q.get('offset'));
    if(failUniverse||(text&&failSearch))return error();
    let rows=securities.filter(row=>(!q.get('exchange')||q.get('exchange')===row.exchange)&&(!q.get('index_group')||groups.groups[q.get('index_group')]?.includes(row.symbol))&&(!q.get('symbols')||q.get('symbols').split(',').includes(row.symbol))&&(!text||[row.symbol,row.display_name_en,row.company_name].join(' ').toLowerCase().includes(text.toLowerCase())));
    const captured=emptyUniverse?{items:[],total:0,total_universe:0,offset,limit:size,status:'not_attempted',last_synced_at:null,index_groups:{groups:{},status:'not_attempted',source:'SSI:FastConnect'}}:{items:rows.slice(offset,offset+size),total:rows.length,total_universe:securities.length,offset,limit:size,status:'healthy',last_synced_at:now,index_groups:groups};
    if(initialHold)await initialHold;
    if(text===delayedQuery){queryStarted?.();await queryHold;}
    try{return await json(captured);}catch{return;}
   }
   if(path==='/api/stocks/live-index')return indexMode==='error'?error():json(indexMode==='unavailable'?{snapshot:null,status:'unavailable',session:'closed',as_of:now}:indexMode==='stale'?{...freshIndex,status:'stale',snapshot:{...freshIndex.snapshot,trading_date:'2026-01-01',updated_at:'2026-01-01T08:00:00Z'}}:indexMode==='down'?{...freshIndex,snapshot:{...freshIndex.snapshot,change:-5.67,change_percent:-0.46}}:indexMode==='unchanged'?{...freshIndex,snapshot:{...freshIndex.snapshot,change:0,change_percent:0}}:freshIndex);
   if(path==='/api/stocks/live')return json({items:Object.fromEntries((q.get('symbols')||'').split(',').map(symbol=>[symbol,{status:'unavailable',snapshot:null}])),session:'closed',as_of:now});
   if(path==='/api/news/hot')return failHot?error():json(emptyHot?[]:stories);
   if(path==='/api/community/pulse')return failCommunity?error():json({...pulse,window:{...pulse.window,kind:q.get('window')||'today',label:q.get('window')==='last24h'?'Last 24 hours':'Today'},...(emptyCommunity?{items:[],themes:[],unique_items:0,active_tickers:[]}: {})});
   if(path==='/api/community/sources'||path==='/api/news/sources')return json([]);
   if(path==='/api/news/feed/page')return json({items:stories.filter((row,n)=>n!==1&&row.research_category===q.get('research_category')),as_of:now,next_offset:null,has_more:false});
   if(path==='/api/news/feed')return json([]);
   if(path.startsWith('/api/technical/'))return json({kind:'diagnostic',ticker:path.split('/')[3],requested_session:null,readiness_status:'INCOMPLETE_EVIDENCE',reason_codes:['missing_calendar'],safe_to_display_as_verified:false});
   if(path.endsWith('/overview')){
    const symbol=path.split('/')[3];
    return json({stock:{id:1,...securities.find(row=>row.symbol===symbol)},history:[],market:{ticker:symbol,as_of:null,close:null,source:'test unavailable'},fundamentals:{period:null,source:'test unavailable'},news:[]});
   }
   if(path.endsWith('/technical-history')||path.endsWith('/fundamentals/history')||path==='/api/stocks/index-history')return json([]);
   return error();
  });
  const stocks=page.locator('section[aria-labelledby="explore-title"]');
  const hot=page.locator('section[aria-labelledby="hot-topics"]');
  const community=page.locator('section[aria-labelledby="community-pulse"]');
  const hero=page.locator('main > div > header');
  await page.goto(base);
  await expect(stocks.getByText('Loading equities…',{exact:true})).toBeVisible();
  releaseInitial();initialHold=null;
  await expect(stocks.getByRole('link',{name:/Research T/})).toHaveCount(10);
  await expect(stocks.getByText('1–10 of 32 results')).toBeVisible();
  await expect(hot.locator('[data-story-id]')).toHaveCount(3);
  await expect(hot.getByRole('link',{name:'Synthetic market story 0',exact:true})).toHaveAttribute('href','https://example.org/story-0');
  await expect(community.getByRole('link',{name:'Original discussion ↗',exact:true}).first()).toHaveAttribute('href',communityItem.url);
  await expect(community.getByText('Discussion activity, not sentiment.',{exact:true})).toBeVisible();
  await expect(community.getByText('Sources need a fresh worker check; coverage is incomplete.',{exact:true})).toBeVisible();
  assert.ok(requests.filter(r=>r.path==='/api/stocks/universe').every(r=>Number(new URLSearchParams(r.query).get('limit'))<=10));
  await expect(hero.getByText('1,234.56',{exact:true})).toBeVisible();
  await expect(hero.getByText('+5.67',{exact:false})).toBeVisible();
  await expect(hero.getByText('Up',{exact:true})).toBeVisible();
  await expect(hero.getByText('Unavailable',{exact:true})).toHaveCount(2);
  await page.screenshot({path:`${out}/home-${viewport.width}-en-dark.png`,fullPage:true});
  console.log(`Home render passed at ${viewport.width}px; checking filters and keyboard search.`);
  await stocks.getByRole('button',{name:'Next',exact:true}).click();
  await expect(stocks.getByText('11–20 of 32 results')).toBeVisible();
  await expect(stocks.getByRole('link',{name:'Research T10',exact:true})).toBeVisible();
  await stocks.getByRole('button',{name:'Previous',exact:true}).click();
  await expect(stocks.getByText('1–10 of 32 results')).toBeVisible();
  for(const exchange of ['HOSE','HNX','UPCOM']){
   await stocks.getByLabel('Exchange',{exact:true}).selectOption(exchange);
   await expect(stocks.locator('[aria-live="polite"]')).toContainText(`of ${securities.filter(row=>row.exchange===exchange).length} results`);
  }
  await stocks.getByLabel('Exchange',{exact:true}).selectOption('');
  await stocks.getByLabel('Index group',{exact:true}).selectOption('VN30');
  await expect(stocks.getByText('1–10 of 12 results')).toBeVisible();
  await stocks.getByLabel('Index group',{exact:true}).selectOption('VN100');
  await expect(stocks.getByText('1–10 of 32 results')).toBeVisible();
  assert.equal(await stocks.locator('option[value="HNX30"]').evaluate(option=>option.disabled),true);
  await stocks.getByLabel('Index group',{exact:true}).selectOption('');
  const search=page.getByRole('combobox',{name:'Search ticker',exact:true});
  await search.focus();await expect(search).toHaveAttribute('aria-expanded','false');
  await search.fill('T01');await expect(page.getByRole('option',{name:/T01/})).toHaveCount(1);
  await search.press('ArrowDown');await expect(search).toHaveAttribute('aria-activedescendant',/.+-0/);
  await search.press('Escape');await expect(search).toHaveAttribute('aria-expanded','false');
  await search.press('ArrowDown');await search.press('Enter');
  await expect(page).toHaveURL(/\/stocks\/T01$/);
  await expect(page.locator('#stock-technical-insights').getByText(/not yet accepted/)).toBeVisible();
  await page.goto(base);await expect(stocks.getByRole('link',{name:/Research T/})).toHaveCount(10);
  await search.focus();await expect(page.getByText('Recent searches',{exact:true})).toBeVisible();
  await expect(page.getByRole('option',{name:/T01/})).toHaveCount(1);
  await page.getByRole('button',{name:'Remove T01 from search history',exact:true}).click();
  assert.deepEqual(await page.evaluate(()=>JSON.parse(localStorage.getItem('vn30.recent-equity-searches.v1'))),[]);
  await page.evaluate(()=>{localStorage.setItem('vn30.recent-equity-searches.v1','["T01","T02"]');window.dispatchEvent(new Event('equity-search'));});
  await search.focus();await expect(page.getByRole('listbox').getByRole('option')).toHaveCount(2);
  await page.getByRole('button',{name:'Clear history',exact:true}).click();
  assert.deepEqual(await page.evaluate(()=>JSON.parse(localStorage.getItem('vn30.recent-equity-searches.v1'))),[]);
  await page.evaluate(()=>{localStorage.setItem('vn30.recent-equity-searches.v1','["MISSING"]');window.dispatchEvent(new Event('equity-search'));});
  await search.press('ArrowDown');await expect(page.getByText('MISSING · Equity metadata unavailable',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Remove MISSING from search history',exact:true}).click();
  assert.deepEqual(await page.evaluate(()=>JSON.parse(localStorage.getItem('vn30.recent-equity-searches.v1'))),[]);
  // An obsolete remote request must not replace newer matches.
  delayedQuery='T01';let releaseQuery;queryHold=new Promise(resolve=>{releaseQuery=resolve;});
  const started=new Promise(resolve=>{queryStarted=resolve;});
  await search.fill('T01');await Promise.race([started,new Promise((_,reject)=>setTimeout(()=>reject(Error('Delayed query did not start')),5000))]);await search.fill('T02');
  await expect(page.getByRole('option',{name:/T02/})).toHaveCount(1);
  releaseQuery();delayedQuery=null;await page.waitForTimeout(100);
  await expect(page.getByRole('option',{name:/T01/})).toHaveCount(0);
  await search.fill('no match');await expect(page.getByText('No matching listed equities.',{exact:true})).toBeVisible();
  failSearch=true;await search.fill('T03');await expect(page.getByText('Equity search unavailable',{exact:false})).toBeVisible();
  failSearch=false;await search.locator('..').getByRole('button',{name:'Retry',exact:true}).click();await expect(page.getByRole('option',{name:/T03/})).toHaveCount(1);
  await search.press('Escape');
  const exploreSearch=stocks.getByRole('combobox',{name:'Explore ticker or company',exact:true});
  await exploreSearch.fill('issuer 31');await expect(stocks.getByText('1–1 of 1 results')).toBeVisible();
  await exploreSearch.fill('no match');await expect(stocks.getByText('No matching equities in the cached universe.',{exact:true})).toBeVisible();
  await stocks.getByRole('button',{name:'Clear search',exact:true}).click();await expect(stocks.getByText('1–10 of 32 results')).toBeVisible();
  failUniverse=true;await stocks.getByRole('button',{name:'Next',exact:true}).click();
  await expect(stocks.getByText('Equity metadata could not be loaded.',{exact:false})).toBeVisible();
  failUniverse=false;await stocks.getByRole('button',{name:'Retry',exact:true}).click();await expect(stocks.getByText('11–20 of 32 results')).toBeVisible();
  await community.getByLabel('Discussion window',{exact:true}).selectOption('last24h');
  await expect(community.getByText(/unique discussion in this bounded sample · Last 24 hours/)).toBeVisible();
  failCommunity=true;await community.getByLabel('Discussion window',{exact:true}).selectOption('today');
  await expect(community.getByText(/temporarily unavailable. Counts are unknown/)).toBeVisible();
  failCommunity=false;await community.getByRole('button',{name:'Retry Community',exact:true}).click();await expect(community.getByText('Synthetic discussion theme',{exact:true})).toBeVisible();
  emptyCommunity=true;await community.getByLabel('Discussion window',{exact:true}).selectOption('last24h');
  await expect(community.getByText(/No last-24-hour discussions/)).toBeVisible();
  emptyCommunity=false;
  for(const mode of ['down','unchanged','stale','unavailable','error']){
   indexMode=mode;await page.reload();await expect(stocks.getByRole('link',{name:/Research T/})).toHaveCount(10);
   if(mode==='down')await expect(hero.getByText('Down',{exact:true})).toBeVisible();
   if(mode==='unchanged')await expect(hero.getByText('Unchanged',{exact:true})).toBeVisible();
   if(mode==='stale'){await expect(hero.getByText('Stale market data',{exact:false})).toBeVisible();await expect(hero.getByText('One-minute index snapshot',{exact:false})).toHaveCount(0);}
   if(mode==='unavailable')await expect(hero.getByText('VN-Index data unavailable.',{exact:false})).toBeVisible();
   if(mode==='error')await expect(hero.getByText('Index data could not be loaded.',{exact:false})).toBeVisible();
  }
  indexMode='fresh';await hero.getByRole('button',{name:'Retry',exact:true}).click();await expect(hero.getByText('Up',{exact:true})).toBeVisible();
  failHot=true;await page.reload();await expect(hot.getByText('Hot Topics is temporarily unavailable.',{exact:false})).toBeVisible();
  failHot=false;await hot.getByRole('button',{name:'Retry',exact:true}).click();await expect(hot.locator('[data-story-id]')).toHaveCount(3);
  emptyHot=true;await page.reload();await expect(hot.getByText('No stories with independent publisher coverage qualify yet.',{exact:true})).toBeVisible();
  emptyHot=false;await page.reload();await expect(hot.locator('[data-story-id]')).toHaveCount(3);
  failImage=true;await page.reload();await expect(hot.getByText('Only reporting with source thumbnails is shown.',{exact:true})).toBeVisible();await expect(hot.locator('[data-story-id]')).toHaveCount(0);
  failImage=false;await page.reload();await expect(hot.locator('[data-story-id]')).toHaveCount(3);
  await hot.getByRole('link',{name:'All news ↗',exact:true}).click();await expect(page).toHaveURL(/\/news$/);
  await page.getByRole('button',{name:'Company',exact:true}).click();
  await expect(page.getByRole('link',{name:'Synthetic market story 0',exact:true})).toHaveCount(1);
  await page.getByRole('button',{name:'Industry',exact:true}).click();await expect(page.getByRole('link',{name:'Synthetic market story 1',exact:true})).toHaveCount(1);
  await page.getByRole('button',{name:'Market',exact:true}).click();await expect(page.getByRole('link',{name:'Synthetic market story 2',exact:true})).toHaveCount(1);
  await page.goto(base);await community.getByRole('link',{name:'All discussions ↗',exact:true}).click();await expect(page).toHaveURL(/\/news\?view=community$/);
  await expect(page.getByText('Synthetic discussion theme',{exact:true})).toBeVisible();
  await page.goto(base);await hero.getByRole('link',{name:/VN-Index/}).click();await expect(page).toHaveURL(/\/indices\/VNINDEX$/);await expect(page.getByRole('heading',{name:'VN-Index research',exact:true})).toBeVisible();
  emptyUniverse=true;await page.goto(base);await expect(stocks.getByText('Equity metadata has not been acquired yet.',{exact:true})).toBeVisible();
  await expect(stocks.getByText('0 Vietnam equities',{exact:true})).toHaveCount(0);await expect(stocks.getByText('0–0 of 0 results',{exact:true})).toHaveCount(0);
  emptyUniverse=false;
  await page.goto(base);await page.getByLabel('Language',{exact:true}).selectOption('vi');
  await expect(page.getByRole('heading',{name:'Chứng khoán Việt Nam',exact:true})).toBeVisible();
  await expect(stocks.getByRole('heading',{name:'Khám phá cổ phiếu',exact:true})).toBeVisible();
  await expect(community.getByText('Số lượng thảo luận không phản ánh tâm lý thị trường.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Chuyển sang giao diện sáng',exact:true}).click();
  await page.screenshot({path:`${out}/home-${viewport.width}-vi-light.png`,fullPage:true});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);
  checks.push({viewport,checks:['home','ten-row-pagination','all-exchanges','VN30','VN100','missing-HNX30','empty-search','ticker-search','company-search','keyboard','recent-reload','individual-remove','unavailable-recent-remove','clear-history','obsolete-response','stock-detail-technical','news-categories-retained','hot-dedup','hot-source-link','broken-source-image','community-window','community-source-link','stale-source','index-up-down-zero-stale-unavailable','loading-empty-errors-retry','unacquired-counts-unknown','index-navigation','EN-VI','dark-light','no-horizontal-overflow']});
  await context.close();
 }
 assert.deepEqual(pageErrors,[]);
 const report={status:'PASS',evidence:'Synthetic browser fixtures only; no market observations invented for product use',checks,pageErrors};
 writeFileSync(`${out}/browser-report.json`,JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));
}finally{await browser.close();}
