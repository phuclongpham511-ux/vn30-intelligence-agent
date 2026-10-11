import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {readLanguage,translate} from '../lib/translations.ts';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
const require=createRequire(import.meta.url);
function component(file,overrides={}) {
  overrides={'./LivePrice':{LivePrices:({children})=>children},'../components/stock/LivePrice':{LivePrices:({children})=>children},'../stock/LivePrice':{TickerMovement:()=>null},...overrides};
  const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{
    filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
  const exports={};
  new Function('require','exports',code)(name=>overrides[name]||require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
  return exports;
}
function render(Component,props={},language='vi') {
  return renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:{...localeTools(language),setLanguage(){}}},React.createElement(Component,props)));
}
const passthrough=({children})=>children;
const button=({variant,asChild,...props})=>React.createElement('button',props);
const article={thumbnail_url:'https://example.org/photo.jpg',id:'a',title:'News',url:'https://example.org/a',source_name:'Company',published_at:null,first_seen_at:'2026-10-06T05:00:00Z',tickers:['XYZ'],topics:[],sectors:[]};

test('saved EN/VI selection overrides browser locale; invalid preference falls back deterministically',()=>{
  assert.equal(readLanguage('en','vi-VN'),'en');
  assert.equal(readLanguage('vi','en-US'),'vi');
  assert.equal(readLanguage(null,'vi-VN'),'vi');
  assert.equal(readLanguage('invalid','fr-FR'),'en');
  assert.equal(readLanguage(null),'en');
});
test('typed UI messages interpolate values without changing tickers or source text',()=>{
  assert.equal(translate('vi','Follow {ticker}',{ticker:'XYZ'}),'Theo dõi XYZ');
  assert.equal(translate('en','Follow {ticker}',{ticker:'XYZ'}),'Follow XYZ');
  assert.equal(translate('vi','News'),'Tin tức');
});

test('Quick News header and loading chrome preserve EN/VI dictionary keys',()=>{
  const {default:News}=component('../app/components/stock/StockNews.tsx',{
    '../news/SourceCoverage':()=>null,'../news/TopStory':()=>null});
  for(const language of ['en','vi']) {
    const html=render(News,{ticker:'XYZ'},language);
    assert.ok(html.includes(translate(language,'Quick news · {ticker}',{ticker:'XYZ'})));
    assert.ok(html.includes(translate(language,'Loading quick news…')));
    assert.doesNotMatch(html,/Â|â€/);
  }
});
test('locale formatting preserves real zero, missing values, precision and Vietnam date boundaries',()=>{
  const vi=localeTools('vi'),en=localeTools('en');
  assert.equal(vi.number(1234.56),'1.234,56');
  assert.equal(en.number(1234.56),'1,234.56');
  assert.equal(vi.number(null),'—');assert.equal(vi.number(0),'0');
  assert.equal(vi.percent(0),'0%');assert.equal(vi.compact(null),'—');
  assert.equal(vi.date('2026-10-05T17:01:00Z'),'06/10/2026');
  assert.match(en.date('2026-10-05T17:01:00Z',true),/6 Oct 2026.*00:01/);
  assert.equal(vi.date('broken'),translate('vi','Unavailable'));
});
test('news chrome localizes while even dictionary-matching source titles and publisher names stay original',()=>{
  const {default:NewsThumbnail}=component('../app/components/news/NewsThumbnail.tsx');
  const {default:TopStory}=component('../app/components/news/TopStory.tsx',{'./NewsThumbnail':NewsThumbnail});
  const props={item:{story:{id:'s',source_count:2},representative_article:article,articles:[article],research_category:'MARKET_BRIEF',ticker_associations:[{symbol:'XYZ',article_id:article.id,article_title:article.title,kind:'explicit_stock',matched_text:'xyz',policy:'issuer-context-v1'}]}};
  for(const language of ['vi','en']) {
    const html=render(TopStory,props,language);
    assert.match(html,/>News<\/a>/);assert.match(html,/>Company<\/span>/);assert.match(html,/>XYZ<\/strong>/);
    assert.doesNotMatch(html,/Market Brief/);
    assert.match(html,language==='vi'?/Bằng chứng/:/Evidence/);
  }
});
test('Community UI translates, source theme/excerpt remains original and unknown counts stay unknown',()=>{
  const {CommunityDiscussions}=component('../app/components/stock/StockCommunity.tsx');
  const item={id:'one',source_id:'forum',title:'News',excerpt:'Company',published_at:'2026-10-06T05:00:00Z',tickers:['XYZ'],replies:null,views:0,url:'https://example.org/thread'};
  const data={window:{label:'Today',start:item.published_at},unique_items:1,items:[item],sources:[],themes:[]};
  const html=render(CommunityDiscussions,{ticker:'XYZ',data,loading:false,error:false,retry(){},showHeading:false});
  assert.match(html,/>News<\/p>/);assert.match(html,/>Company<\/p>/);
  assert.match(html,/Chưa có số phản hồi/);assert.match(html,/0 lượt xem/);
  assert.doesNotMatch(html,/<h2/);
});
test('stock search and unavailable states render natural Vietnamese without translating caller data',()=>{
  const {default:Search}=component('../app/components/stock/StockSearch.tsx',{'./useRecentSearches':{useRecentSearches:()=>({recent:[],remember(){}})}});
  const html=render(Search,{stocks:[],label:'Stock to follow',onSelect(){}});
  assert.match(html,/aria-label="Cổ phiếu muốn theo dõi"/);assert.match(html,/placeholder="Tìm mã hoặc doanh nghiệp"/);
  const {StockError}=component('../app/components/stock/StockStates.tsx',{'../mascot/Mascot':{MascotIllustration:()=>null},'../ui/button':{Button:button},'../ui/skeleton':{Skeleton:()=>null}});
  assert.match(render(StockError,{ticker:'XYZ',message:'The data provider is temporarily unavailable. Please try again.',retry(){}}),/Nguồn dữ liệu tạm thời chưa khả dụng/);
});
test('News navigation translates all four ordered tabs and does not repeat category headings',()=>{
  const {default:News}=component('../app/news/page.tsx',{
    '../components/mascot/Mascot':{MascotState:passthrough},'../components/ui/button':{Button:button},
    '../components/news/SourceCoverage':()=>null,'../components/news/TopStory':()=>null,'../components/news/CommunityPulse':()=>null});
  for(const language of ['en','vi']) {
    const html=render(News,{},language);
    const labels=language==='vi'?['Ngành','Doanh nghiệp','Thị trường','Cộng đồng']:['Industry','Company','Market','Community Pulse'];
    let previous=-1;
    for(const label of labels){const index=html.indexOf(`>${label}</button>`);assert.ok(index>previous);previous=index;}
    assert.doesNotMatch(html,/<h2|Market Brief|Broad Vietnam market/);
  }
});
test('Woofi shell uses local supplied logo, compact language control and no Daily data header label',()=>{
  const {default:Shell}=component('../app/components/app-shell/AppShell.tsx',{
    'next/navigation':{usePathname:()=>'/news'},'next-themes':{ThemeProvider:passthrough,useTheme:()=>({resolvedTheme:'dark',setTheme(){}})},
    '@/lib/i18n':{useLocale:()=>({...localeTools('vi'),setLanguage(){}}),LanguageProvider:passthrough},
    '../stock/TickerSearch':()=>React.createElement('input',{'aria-label':'search'}),'../stock/StockUniverse':{StockUniverse:passthrough},
    '../ui/button':{Button:button},'../ui/sheet':{Sheet:passthrough,SheetTrigger:()=>null,SheetContent:()=>null,SheetTitle:passthrough,SheetDescription:passthrough}});
  const html=render(Shell,{children:'content'});
  assert.match(html,/src="\/assets\/woofi-logo.png"/);assert.match(html,/alt="Woofi"/);
  assert.match(html,/aria-label="Ngôn ngữ"/);assert.match(html,/Giới thiệu Woofi/);
  assert.doesNotMatch(html,/Daily data|VN30 Intelligence|Vietnam Equity Intelligence/);
});

test('real ticker renderer uses yellow zero, neutral missing, and exposes the stale reference session',()=>{
 const snapshot={ticker:'XYZ',last_price:10000,reference_price:10000,change:0,change_percent:0,trading_date:'2026-10-09',updated_at:'2026-10-09T07:45:00Z',source:'Fixture:test',session:'closed'};
 const {LivePrices,LivePrice,TickerMovement}=component('../app/components/stock/LivePrice.tsx',{'@/lib/useLiveMarket':{useLiveMarket:()=>({data:{items:{XYZ:{status:'stale',snapshot}},session:'closed'},failed:false})}});
 const tree=React.createElement(LivePrices,{symbols:['XYZ'],interval:30000},React.createElement(React.Fragment,null,React.createElement(LivePrice,{symbol:'XYZ'}),React.createElement(TickerMovement,{symbol:'XYZ'}),React.createElement(TickerMovement,{symbol:'MISSING'})));
 const html=render(()=>tree,{},'en');
 assert.match(html,/class="unchanged"/);assert.match(html,/0.00%/);assert.match(html,/Stale market data/);assert.match(html,/9 Oct 2026/);assert.match(html,/class="text-muted-foreground"/);assert.match(html,/Market data unavailable/);
});
test('raw source evidence stays inspectable when its thumbnail is missing',()=>{
 const {default:Thumbnail}=component('../app/components/news/NewsThumbnail.tsx');
 const {default:Row}=component('../app/components/news/ArticleRow.tsx',{'./NewsThumbnail':Thumbnail});
 const props={article:{...article,thumbnail_url:null}};
 assert.equal(render(Row,props),'');
 const raw=render(Row,{...props,requireImage:false});
 assert.match(raw,/News/);assert.match(raw,/https:\/\/example.org\/a/);assert.match(raw,/Chưa xác minh/);assert.doesNotMatch(raw,/href="\/stocks\/XYZ"/);
 const linked=render(Row,{...props,requireImage:false,associations:[{symbol:'XYZ',article_id:article.id,article_title:article.title,kind:'explicit_stock',matched_text:'xyz',policy:'issuer-context-v1'}]});
 assert.match(linked,/href="\/stocks\/XYZ"/);assert.match(linked,/Ngữ cảnh doanh nghiệp: xyz/);
});

test('actual News card never renders legacy ticker chips, but retains qualified issuer navigation',()=>{
 const {default:Thumbnail}=component('../app/components/news/NewsThumbnail.tsx');
 const {default:TopStory}=component('../app/components/news/TopStory.tsx',{'./NewsThumbnail':Thumbnail});
 const item={story:{id:'s',source_count:1},representative_article:{...article,title:'Tỷ giá USD giảm',tickers:['USD']},articles:[article]};
 for(const language of ['vi','en']){
  const html=render(TopStory,{item},language);assert.match(html,/Tỷ giá USD giảm/);assert.doesNotMatch(html,/ticker-chip|\/stocks\/USD|Mentioned stocks|Cổ phiếu được nhắc đến/);
  const qualified={...item,representative_article:{...item.representative_article,title:'Cổ phiếu USD tăng giá'},ticker_associations:[{symbol:'USD',article_id:'a',article_title:'Cổ phiếu USD tăng giá',kind:'explicit_stock',matched_text:'usd',policy:'issuer-context-v1'}]};
  assert.match(render(TopStory,{item:qualified},language),/href="\/stocks\/USD"/);
 }
});
