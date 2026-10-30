import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';

const require=createRequire(import.meta.url);
function component(file,mocks={}){
 const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 const exports={};new Function('require','exports',code)(name=>mocks[name]||require(name.startsWith('@/lib/')?'../lib/'+name.slice(6)+'.ts':name),exports);return exports.default;
}
const render=(Component,props,language='en')=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools(language)},React.createElement(Component,props)));

test('news cards keep primary story details and ticker links while omitting expandable provenance',()=>{
 const Card=component('../app/components/news/TopStory.tsx',{'./NewsThumbnail':({children})=>children,'../stock/LivePrice':{TickerMovement:()=>null}});
 const article={id:'lead',title:'FPT announces quarterly results',url:'https://publisher.example/fpt',source_name:'Publisher A',published_at:'2026-10-26T08:30:00Z',first_seen_at:'2026-10-26T08:35:00Z',last_seen_at:'2026-10-27T08:00:00Z',tickers:['FPT'],topics:[],sectors:[]};
 const sibling={...article,id:'copy',title:'Repeated copy headline',source_name:'Publisher B',url:'https://publisher.example/copy',published_at:null,first_seen_at:'2026-10-26T08:40:00Z'};
 const item={story:{id:'fpt-results',source_count:2},representative_article:article,articles:[article,sibling],ticker_associations:[{symbol:'FPT',article_id:'lead',article_title:article.title,article_url:article.url,kind:'explicit_stock',matched_text:'FPT',policy:'issuer-context-v2',evidence_origin:'headline'}]};
 const before=JSON.stringify(item);
 for(const category of ['COMPANY','INDUSTRY','MARKET_BRIEF']){
  const html=render(Card,{item:{...item,research_category:category},compact:true,textOnly:true,showThumbnail:false});
  assert.match(html,/FPT announces quarterly results/);
  assert.match(html,/Publisher A/);
  assert.match(html,/dateTime="2026-10-26T08:30:00Z"/);
  assert.match(html,/href="\/stocks\/FPT"/);
  for(const diagnostic of ['Sources and timestamps','independent publisher','Latest reporting','First seen','Repeated copy headline','View source archive','news/stories/fpt-results'])assert.doesNotMatch(html,new RegExp(diagnostic,'i'));
 }
 assert.equal(JSON.stringify(item),before);
});

test('news category tabs use larger theme-token controls on desktop and mobile',()=>{
 const postcss=require('postcss');
 const css=postcss.parse(readFileSync(new URL('../app/market-workspace.css',import.meta.url),'utf8'));
 const declarations=(rule)=>Object.fromEntries(rule.nodes.filter(node=>node.type==='decl').map(node=>[node.prop,node.value]));
 const base=css.nodes.find(node=>node.type==='rule'&&node.selector==='.news-section-nav button');
 assert.ok(base);
 const baseStyle=declarations(base);
 assert.equal(baseStyle['font-size'],'14px');
 assert.equal(baseStyle['font-weight'],'600');
 assert.equal(baseStyle['min-height'],'46px');
 assert.equal(baseStyle.padding,'9px 15px');
 assert.match(baseStyle.color,/var\(--muted-foreground\)/);
 const active=css.nodes.find(node=>node.type==='rule'&&node.selector==='.news-section-nav button[aria-pressed=true]');
 assert.match(declarations(active).color,/var\(--primary\)/);
 assert.match(declarations(active)['font-weight'],/^(700|bold)$/);
 const light=css.nodes.find(node=>node.type==='rule'&&node.selector==='.market-shell');
 const dark=css.nodes.find(node=>node.type==='rule'&&node.selector==='.dark .market-shell');
 for(const theme of [declarations(light),declarations(dark)]){
  assert.ok(theme['--primary']);
  assert.ok(theme['--muted-foreground']);
  assert.ok(theme['--border']);
 }
 const mobile=css.nodes.find(node=>node.type==='atrule'&&node.params.includes('760px'));
 const mobileButton=mobile.nodes.find(node=>node.type==='rule'&&node.selector==='.news-section-nav button');
 const mobileStyle=declarations(mobileButton);
 assert.equal(mobileStyle['min-height'],'44px');
 assert.equal(mobileStyle['font-size'],'14px');
 assert.equal(mobileStyle.padding,'8px 12px');
});
