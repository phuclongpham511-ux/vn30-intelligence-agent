// Offline acceptance responses only. Imported only by tests and the snapshot builder.
import {fixture as financialFixture} from './fundamental-summary.mjs';
import {at,article,news,thread,discussion,source,forum} from './stock-intelligence.mjs';

export const clock=at;
export function acceptanceDataset(savedFinancials={}) {
 const financial=structuredClone(financialFixture());
 financial.is_fixture=true;financial.source='DEMO synthetic financial contract';
 financial.read_at=at;financial.limitations=['DEMO: synthetic contract; not an issuer disclosure.'];
 for(const row of [...financial.rows,...financial.chart_rows]){row.is_fixture=true;row.source=financial.source;}
 for(const metric of financial.fundamental_summary.metrics)if(metric.value!==null){metric.status='DEMO';metric.reason='Synthetic financial evidence';}
 const action={symbol:'ABC',action_id:'demo-action',observation_id:'demo-action-v1',observed_at:at,action_type:'cash_dividend',effective_date:null,record_date:null,payment_date:null,announced_at:null,announced_on:null,source:'DEMO synthetic source — no original disclosure',source_url:null,supporting_urls:[],source_title:'DEMO withheld event facts',evidence_text:'Synthetic state fixture. No issuer publication, event dates or cash amount is asserted.',source_revision:'demo-v1',source_updated_at:null,verification_note:null,verified:true,withdrawn:false,is_fixture:true,terms:null};
 return {clock:at,financials:{ABC:{annual:financial},...savedFinancials},
  stocks:['AAA','ABC','BBB'].map(symbol=>({symbol,exchange:'DEMO',company_name:'Công ty giả lập '+symbol,display_name_en:'DEMO research company '+symbol,source:'DEMO identity fixture',instrument_type:'equity',last_synced_at:at})).concat(savedFinancials.FPT?[{symbol:'FPT',exchange:'HOSE',company_name:'FPT · saved financial replay',display_name_en:'FPT · saved financial replay',source:'Replay identifier; company metadata not qualified',instrument_type:'equity',last_synced_at:null}]:[]),
  actions:{ABC:[action,{...action,action_id:'demo-pending',observation_id:'demo-pending-v1',action_type:'rights_offering',verified:false},{...action,action_id:'demo-conflict',observation_id:'demo-conflict-v2',action_type:'bonus_shares',verification_note:'Unresolved correction: DEMO conflicting source observations'},{...action,action_id:'demo-withdrawn',observation_id:'demo-withdrawn-v1',action_type:'stock_dividend',withdrawn:true}]},
  // One stable story with two source articles, plus an older story outside 72h.
  articles:[{...article,source_name:'DEMO Publisher',is_fixture:true,tickers:['AAA','ABC','BBB']},{...article,id:'article-copy',url:'https://publisher.example/copy',source_name:'DEMO Wire',is_fixture:true,tickers:['AAA','ABC','BBB']}],
  stories:[{...news,title:'DEMO: AAA company results',revision_members:{article:'v1','article-copy':'v1'},evidence:[]},{...news,id:'news:outside-window',entity_id:'outside-window',occurred_at:'2026-10-14T04:59:59Z',evidence:[]}],
  discussion:{...discussion,title:'DEMO: AAA original discussion',url:'https://forum.example/thread',evidence:{...thread,title:'DEMO: AAA original discussion',tickers:['AAA','ABC','BBB'],source_id:'demo_forum',is_fixture:true,url:'https://forum.example/thread'}},
  news_sources:[{...source,source_id:'demo_publisher',name:'DEMO Publisher'},{...source,source_id:'demo_wire',name:'DEMO Wire'}],
  community_sources:[{...forum,source_id:'demo_forum',name:'DEMO Forum — unverified'}]};
}

// No fetch, filesystem write, provider, database, worker or scheduler in this handler.
export function replayHandler(dataset) {
 const page=(items,hours)=>({items,has_more:false,truncated:false,window_start:new Date(Date.parse(dataset.clock)-hours*3600000).toISOString()});
 const known=symbol=>dataset.stocks.some(row=>row.symbol===symbol);
 const diagnostics=ticker=>({kind:'diagnostic',ticker,requested_session:null,readiness_status:'UNAVAILABLE',reason_codes:['DEMO_NO_TECHNICAL_ACQUISITION'],safe_to_display_as_verified:false});
 const headers={'Cache-Control':'no-store','X-Woofi-Acceptance':'OFFLINE_REPLAY_ONLY'};
 const reply=(body,status=200)=>Response.json(body,{status,headers});
 return async request=>{
  const url=new URL(request.url),path=url.pathname,p=url.searchParams;
  if(request.method==='GET'&&path==='/api/acceptance')return reply({kind:'OFFLINE_REPLAY_ONLY',clock:dataset.clock,storage:'woofi.acceptance.watchlist.v1',symbols:dataset.stocks.map(row=>row.symbol)});
  if(request.method==='GET'&&path==='/api/stocks/universe') {
   const limit=Math.max(1,Math.min(500,Number(p.get('limit')||10))),offset=Math.max(0,Number(p.get('offset')||0));
   const symbols=p.has('symbols')?p.get('symbols').split(','):null;
   const rows=dataset.stocks.filter(row=>(!symbols||symbols.includes(row.symbol))&&(!p.get('q')||JSON.stringify(row).toLowerCase().includes(p.get('q').toLowerCase())));
   return reply({items:rows.slice(offset,offset+limit),total:rows.length,total_universe:dataset.stocks.length,offset,limit,status:'DEMO',last_synced_at:dataset.clock,index_groups:{groups:{VN30:['AAA','ABC','BBB']},status:'DEMO',source:'DEMO invented membership'}});
  }
  if(request.method==='GET'&&path==='/api/stocks/live')return reply({as_of:dataset.clock,session:'unknown',items:Object.fromEntries((p.get('symbols')||'').split(',').filter(Boolean).map(ticker=>[ticker,{status:'unavailable',snapshot:null}]))});
  if(request.method==='POST'&&path==='/api/stocks/live-release')return reply({released:true,fixture:true});
  if(request.method==='POST'&&path==='/api/watchlists/intelligence') {
   if(Number(request.headers.get('content-length')||0)>8000)return reply({detail:'Request too large'},413);
   let body;try{const text=await request.text();if(text.length>8000)return reply({detail:'Request too large'},413);body=JSON.parse(text);}catch{return reply({detail:'Invalid request'},422);}
   if(!Array.isArray(body.symbols)||body.symbols.length>50||body.symbols.some(s=>typeof s!=='string'||!/^[A-Z0-9]{1,20}$/.test(s))||new Set(body.symbols).size!==body.symbols.length||!Number.isInteger(body.offset??0)||(body.offset??0)<0||(body.page_size??12)!==12)return reply({detail:'Invalid request'},422);
   const stocks=body.symbols.map(symbol=>{
    if(!known(symbol))return {symbol,status:'unavailable',news:null,community:null,technical:null};
    const articles=dataset.articles.map(a=>({...a,title:dataset.stories[0].title}));
    const cutoff=Date.parse(dataset.clock)-72*3600000;
    const stories=dataset.stories.filter(s=>Date.parse(s.occurred_at)>=cutoff&&Date.parse(s.occurred_at)<=Date.parse(dataset.clock)).map(s=>({...s,evidence:articles,source_count:articles.length}));
    const communityCutoff=Date.parse(dataset.clock)-24*3600000;
    const comments=Date.parse(dataset.discussion.occurred_at)>=communityCutoff&&Date.parse(dataset.discussion.occurred_at)<=Date.parse(dataset.clock)?[dataset.discussion]:[];
    const info=dataset.stocks.find(row=>row.symbol===symbol),offset=body.offset??0;
    return {...info,status:'ready',news:page(stories.slice(offset,offset+12),72),community:{...page(comments.slice(offset,offset+12),24),...(body.community_groups?{display_groups:comments.slice(offset,offset+12).map(item=>[item.entity_id])}:{})},technical:{...page([],24),data:diagnostics(symbol)}};
   });
   return reply({as_of:dataset.clock,offset:body.offset??0,page_size:12,stocks,news_sources:dataset.news_sources,community_sources:dataset.community_sources});
  }
  const stock=path.match(/^\/api\/stocks\/([A-Z0-9]{1,20})\/(financials|corporate-actions|market|technical-history)$/);
  if(request.method==='GET'&&stock&&known(stock[1])) {
   const [,symbol,kind]=stock;
   if(kind==='financials'){const frequency=p.get('frequency')||'annual';const data=dataset.financials[symbol]?.[frequency];return data?reply(data):reply({detail:'No qualified replay financial contract for this period'},404);}
   if(kind==='corporate-actions')return reply({ticker:symbol,as_of:dataset.clock,coverage:'INCOMPLETE',items:dataset.actions[symbol]||[],has_more:false});
   if(kind==='market')return reply({ticker:symbol,as_of:null,close:null,source:'DEMO unavailable daily analytics'});
   return reply([]);
  }
  if(request.method==='GET'&&/^\/api\/technical\/[A-Z0-9]+\/daily\/operational\/latest$/.test(path))return reply(diagnostics(path.split('/')[3]));
  return reply({detail:'Not included in offline replay; no backend fallback'},404);
 };
}
