import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
import {indexUiState} from '../lib/marketIndex.ts';
import {mascotAssets,mascotUiStates} from '../lib/mascot.ts';
const require=createRequire(import.meta.url);
function load(file,overrides={}){const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;const exports={};new Function('require','exports',code)(name=>overrides[name]??require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);return exports;}
const render=(View,props={},language='en')=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools(language)},React.createElement(View,props)));
const passthrough=({children})=>children;
const find=(tree,fn)=>{if(!tree||typeof tree!=='object')return; if(fn(tree))return tree;for(const child of React.Children.toArray(tree.props?.children)){const result=find(child,fn);if(result)return result;}};
const now=new Date('2026-10-19T03:00:00Z');
const index=(change=1,patch={})=>({status:'fresh',session:'active',as_of:now.toISOString(),snapshot:{index:'VNINDEX',level:1234.56,change,change_percent:change===null?null:change/10,trading_date:'2026-10-19',updated_at:now.toISOString(),source:'SYNTHETIC TEST INDEX',total_value:null,total_volume:null,...patch}});

test('index mascot uses known fresh direction only; stale, missing, failed and pending remain distinct',()=>{
 assert.equal(indexUiState(null,false,now),'loading');assert.equal(indexUiState(null,true,now),'dataUnavailable');
 assert.equal(indexUiState({...index(),snapshot:null,status:'unavailable'},false,now),'noMatches');
 for(const [change,expected] of [[1,'marketUp'],[-1,'marketDown'],[0,'marketNeutral'],[null,'marketUncertain'],[NaN,'marketUncertain']])assert.equal(indexUiState(index(change),false,now),expected);
 for(const data of [{...index(),status:'stale'},index(1,{updated_at:'2026-10-18T03:00:00Z'}),index(-1,{updated_at:'2026-10-19T02:57:00Z'})])assert.equal(indexUiState(data,false,now),'marketUncertain');
 assert.equal(indexUiState(index(1),true,now),'marketUncertain');
 for(const state of ['marketUp','marketDown','marketNeutral','loading','noMatches','dataUnavailable'])assert.ok(existsSync(new URL('../public'+mascotAssets[mascotUiStates[state]],import.meta.url)));
});

const Context=load('../app/components/market/MarketContext.tsx',{'../mascot/Mascot':{MascotIllustration:({state,size})=>React.createElement('span',{'data-mascot':state,'data-size':size})},'@/lib/useLiveMarket':{useLiveIndex:()=>({data:null,failed:false})}}).MarketContextView;
test('prominent VN-Index exposes absolute and percentage movement, original source/time and guarded states in EN/VI',()=>{
 for(const language of ['en','vi']){
  const html=render(Context,{data:index(),failed:false,refresh(){},prominent:true,now},language);
  assert.match(html,/market-context-prominent/);assert.match(html,/market-index-value/);assert.match(html,/SYNTHETIC TEST INDEX/);assert.match(html,/dateTime="2026-10-19T03:00:00.000Z"/);assert.match(html,/data-mascot="marketUp"/);
  assert.ok(html.includes(localeTools(language).number(1234.56)));assert.ok(html.includes('+1'));assert.ok(html.includes('%'));assert.ok(html.includes(localeTools(language).t('Active trading session')));
  const loading=render(Context,{data:null,failed:false,refresh(){},prominent:true,now},language);assert.match(loading,/data-mascot="loading"/);assert.ok(loading.includes(localeTools(language).t('Loading index…')));
  const failed=render(Context,{data:null,failed:true,refresh(){},prominent:true,now},language);assert.match(failed,/data-mascot="dataUnavailable"/);assert.match(failed,/role="alert"/);assert.ok(failed.includes(localeTools(language).t('Retry')));
 }
 const stale=render(Context,{data:{...index(0),status:'stale'},failed:false,refresh(){},prominent:true,now});assert.match(stale,/data-mascot="marketUncertain"/);assert.match(stale,/market-index-change text-muted-foreground/);assert.match(stale,/Stale market data/);
 const compact=render(Context,{data:index(),failed:false,refresh(){},now});assert.doesNotMatch(compact,/market-context-prominent|data-mascot/);
});

test('desktop navigation toggles labels without removing route links, active identity or native keyboard affordances',()=>{
 let expanded=true;
 const Shell=load('../app/components/app-shell/AppShell.tsx',{react:{...React,useState:()=>[expanded,next=>expanded=typeof next==='function'?next(expanded):next]},'@/lib/i18n':{useLocale:()=>localeTools('en'),LanguageProvider:passthrough},'../ui/button':{Button:passthrough},'../stock/TickerSearch':()=>null,'../stock/StockUniverse':{StockUniverse:passthrough},'../market/MarketSearch':{MarketSearchProvider:passthrough},'next-themes':{ThemeProvider:passthrough}});
 let tree=Shell.PrimaryNavigation({path:'/news'}),html=renderToStaticMarkup(tree);assert.match(html,/aria-expanded="true"/);assert.match(html,/data-expanded="true"/);
 find(tree,n=>n.type==='button').props.onClick();tree=Shell.PrimaryNavigation({path:'/news'});html=renderToStaticMarkup(tree);
 assert.match(html,/aria-expanded="false"/);assert.match(html,/data-expanded="false"/);assert.equal((html.match(/<a /g)||[]).length,3);assert.equal((html.match(/aria-current="page"/g)||[]).length,1);
 for(const label of ['Market','News','Watchlist'])assert.ok(html.includes('aria-label="'+label+'"'));
 assert.match(html,/aria-controls="woofi-primary-destinations"/);assert.doesNotMatch(html,/<aside|role="menu"/);
});

const Thumbnail=load('../app/components/news/NewsThumbnail.tsx').default;
const TopStory=load('../app/components/news/TopStory.tsx',{'./NewsThumbnail':Thumbnail,'../stock/LivePrice':{TickerMovement:()=>{throw Error('Homepage must not add quote consumers');}}}).default;
test('homepage thumbnail keeps representative priority and same-story fallback without financial quote consumers',()=>{
 const article={id:'a',title:'Original long source headline '.repeat(15),url:'https://publisher.example/a',source_name:'Original Publisher',published_at:null,first_seen_at:now.toISOString(),tickers:[],thumbnail_url:'https://publisher.example/image.jpg'};
 const item={story:{id:'one',source_count:2},representative_article:article,articles:[article,{...article,id:'b',thumbnail_url:'https://publisher.example/sibling.jpg'}],thumbnail_url:'https://unrelated.example/image.jpg'};
 let html=render(TopStory,{item,compact:true,textOnly:true,showThumbnail:true});assert.match(html,/src="https:\/\/publisher.example\/image.jpg"/);assert.doesNotMatch(html,/src="https:\/\/unrelated/);assert.match(html,/news-thumbnail/);assert.match(html,/loading="lazy"/);assert.match(html,/First seen/);
 const noImage={...item,representative_article:{...article,thumbnail_url:'javascript:bad'},articles:[]};
 html=render(TopStory,{item:noImage,compact:true,textOnly:true,showThumbnail:true});assert.match(html,/data-thumbnail-status="unavailable"/);assert.doesNotMatch(html,/<img/);assert.match(html,/Original long source headline/);
});

test('failed thumbnail candidates progress to a stable reserved fallback, never hiding the story',()=>{
 let failed=[];const Thumb=load('../app/components/news/NewsThumbnail.tsx',{react:{...React,useState:()=>[failed,fn=>failed=fn(failed)],useEffect(){}}}).default;
 const props={images:['javascript:bad','https://publisher.example/one.jpg','https://publisher.example/two.jpg'],required:false,reserveSpace:true,compact:true,children:image=>image};
 let tree=Thumb(props);assert.equal(find(tree,n=>n.type==='img').props.src,props.images[1]);find(tree,n=>n.type==='img').props.onError();
 tree=Thumb(props);assert.equal(find(tree,n=>n.type==='img').props.src,props.images[2]);find(tree,n=>n.type==='img').props.onError();
 const html=renderToStaticMarkup(Thumb(props));assert.match(html,/data-thumbnail-status="unavailable"/);assert.doesNotMatch(html,/<img/);
});

const Quote=load('../app/components/stock/QuoteMap.tsx',{'./LivePrice':{useLivePrices:()=>({data:null,failed:false})},'./TradingActivity':{__esModule:true,default:()=>null},'./ProvisionalEvidence':()=>null}).QuoteMapView;
const quote=(patch={})=>({ticker:'DEMO01',last_price:10700,reference_price:10000,change:700,change_percent:7,price_unit:'VND',trading_date:'2026-10-19',updated_at:now.toISOString(),session:'active',source:'SYNTHETIC TEST',price_limits:{symbol:'DEMO01',trading_date:'2026-10-19',effectiveness:'trading_day',reference_price:10000,unit:'VND',source:'SYNTHETIC TEST',qualification:'qualified',ceiling:10700,floor:9300,ceiling_field:'demo_ceiling',floor_field:'demo_floor'},...patch});
for(const [state,row,status='fresh',failed=false] of [['CEILING',quote()],['ADVANCING',quote({price_limits:undefined})],['REFERENCE',quote({last_price:10000,change:0,change_percent:0})],['DECLINING',quote({last_price:9800,change:-200,change_percent:-2})],['FLOOR',quote({last_price:9300,change:-700,change_percent:-7})],['STALE',quote(),'stale'],['UNAVAILABLE',null,'unavailable'],['UNKNOWN',quote({change:null})],['ERROR',quote(),'fresh',true]])test('full movement cell obeys central price state: '+state,()=>{
 const before=JSON.stringify(row),data={session:'active',as_of:now.toISOString(),items:{DEMO01:{status,snapshot:row}}};
 const html=render(Quote,{stocks:[{symbol:'DEMO01'}],data,failed,now,scope:'page',mode:'board'});
 assert.match(html,new RegExp('<td[^>]*data-movement-state="'+state+'"[^>]*>'));assert.match(html,/quote-movement-cell/);assert.match(html,new RegExp('price-'+state.toLowerCase()));assert.equal(JSON.stringify(row),before);
 const heatmap=render(Quote,{stocks:[{symbol:'DEMO01'}],data,failed,now,scope:'page',mode:'heatmap'});assert.doesNotMatch(heatmap,/quote-movement-cell/);assert.match(heatmap,/Equal cell area, not capitalization/);
});

test('full-cell fills use existing price tokens with readable contrast in both market themes',()=>{
 const postcss=require('postcss'),price=postcss.parse(readFileSync(new URL('../app/price-state.css',import.meta.url),'utf8')),market=postcss.parse(readFileSync(new URL('../app/market-workspace.css',import.meta.url),'utf8'));
 const variables=(ast,selector)=>{const result={};ast.walkRules(selector,r=>r.walkDecls(d=>{if(d.prop.startsWith('--'))result[d.prop]=d.value;}));return result;};
 const luminance=hex=>{let h=hex.replace('#','');if(h.length===3)h=[...h].map(c=>c+c).join('');const [r,g,b]=[0,2,4].map(i=>parseInt(h.slice(i,i+2),16)/255).map(c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4);return .2126*r+.7152*g+.0722*b;};
 const contrast=(a,b)=>{const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);};
 for(const dark of [false,true]){
  const vars={...variables(price,':root'),...variables(market,'.market-shell'),...(dark?{...variables(price,'.dark'),...variables(market,'.dark .market-shell')}:{})};
  const resolve=v=>v.startsWith('var(')?resolve(vars[v.slice(4,-1)]):v;
  for(const [state,token] of [['ceiling','--price-ceiling'],['advancing','--positive'],['reference','--unchanged'],['declining','--negative'],['floor','--price-floor']]){
   let rule;price.walkRules('.quote-table td.quote-movement-cell.price-'+state,r=>rule=r);assert.ok(rule);
   const declaration=key=>rule.nodes.find(n=>n.prop===key)?.value;
   assert.equal(declaration('background'),'var('+token+')');assert.equal(declaration('color'),'var(--price-movement-ink)');assert.ok(contrast(resolve(declaration('background')),resolve(declaration('color')))>=4.5,state+' contrast '+(dark?'dark':'light'));
  }
  assert.ok(contrast(resolve(vars['--muted']),resolve(vars['--muted-foreground']))>=4.5);
 }
 let cell;price.walkRules('.quote-table td.quote-movement-cell',r=>cell=r);assert.equal(cell.nodes.find(n=>n.prop==='border-radius').value,'0');assert.equal(cell.nodes.find(n=>n.prop==='text-align').value,'right');
});

test('responsive styles retain mobile labels after desktop collapse and reserve compact media/index space',()=>{
 const postcss=require('postcss'),ast=postcss.parse(readFileSync(new URL('../app/market-workspace.css',import.meta.url),'utf8'));
 const rules=selector=>{const list=[];ast.walkRules(selector,r=>list.push(r));return list;};const prop=(r,key)=>r.nodes.find(n=>n.prop===key)?.value;
 assert.ok(rules('.woofi-navigation[data-expanded=false] .woofi-nav-label').some(r=>r.parent.params==='(max-width:900px)'&&prop(r,'opacity')==='1'));
 assert.ok(rules('.woofi-navigation-toggle').some(r=>r.parent.params==='(max-width:900px)'&&prop(r,'display')==='none'));
 assert.ok(rules('.woofi-nav-label').some(r=>r.parent.params==='(prefers-reduced-motion:reduce)'&&prop(r,'transition')==='none'));
 for(const selector of ['.hot-topics-stories .news-thumbnail','.market-context-prominent>.market-index-mascot'])assert.ok(rules(selector).every(r=>prop(r,'width')&&prop(r,'height')));
 const sizes=rules('.market-index-value').map(r=>prop(r,'font-size')).filter(Boolean);assert.deepEqual(sizes,['32px','28px']);
 assert.ok(rules('.market-context-prominent').every(r=>prop(r,'grid-template-columns')?.includes('minmax(0,1fr)')));
});
