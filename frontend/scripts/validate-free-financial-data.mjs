// Saved real API contracts and server rendering; no browser, server or network.
import assert from 'node:assert/strict';
import {readFileSync,readdirSync,writeFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {resolve,join} from 'node:path';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
import {observedIndustryData,industryData} from '../lib/industry-financials.ts';
const [directory,report]=process.argv.slice(2);
if(!directory||!report)throw Error('Usage: node scripts/validate-free-financial-data.mjs PRIVATE_API_DIRECTORY REPORT_JSON');
const require=createRequire(import.meta.url);
function component(file){
 const exports={};
 const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 new Function('require','exports',code)(name=>name==='./useStockRead'?{useStockRead:()=>{throw Error('Unexpected acquisition');}}:name==='../ui/button'?{Button:({variant,...props})=>React.createElement('button',props)}:require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
 return exports;
}
const industry=component('../app/components/stock/IndustryDashboard.tsx');
const actions=component('../app/components/stock/StockActions.tsx');
function render(Component,props,language){return renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:{...localeTools(language),setLanguage(){}}},React.createElement(Component,props)));}
const categories=[];
for(const name of readdirSync(join(directory,'industries')).filter(n=>/^\d+\.json$/.test(n))){
 const data=JSON.parse(readFileSync(join(directory,'industries',name),'utf8'));
 observedIndustryData(data,data.industry.id,data.period,true);
 assert.throws(()=>observedIndustryData(data,data.industry.id,data.period));
 assert.throws(()=>industryData(data,data.industry.id,data.period));
 for(const language of ['en','vi']){
  const html=render(industry.ObservedIndustryDashboard,{data},language);
  assert.ok(html.includes(data.classification_source));
  assert.ok(html.includes(data.period));
  assert.ok(!html.includes('NaN')&&!html.includes('Infinity'));
 }
 categories.push(data.industry.id);
}
const dividends=[];
for(const name of readdirSync(join(directory,'dividends')).filter(n=>/^[A-Z0-9]+\.json$/.test(n))){
 const data=JSON.parse(readFileSync(join(directory,'dividends',name),'utf8'));
 assert.equal(data.display_scope,'personal_research');
 assert.equal(data.coverage,'INCOMPLETE');
 const props={ticker:data.ticker,data,retry(){},allowPersonal:true};
 for(const language of ['en','vi']){
  const html=render(actions.StockActionsView,props,language);
  assert.equal((html.match(/data-action-observation=/g)||[]).length,data.items.length);
  for(const row of data.items){
   assert.equal(row.symbol,data.ticker);assert.equal(row.effective_date,null);
   assert.equal(row.announced_at,null);assert.ok(row.announced_on);
   assert.ok(html.includes(row.source_url));
  }
 }
 const publicHtml=render(actions.StockActionsView,{...props,allowPersonal:false},'en');
 assert.equal((publicHtml.match(/data-action-observation=/g)||[]).length,0);
 dividends.push({ticker:data.ticker,observations:data.items.length});
}
assert.ok(categories.length&&dividends.length);
const result={contract:'free-data-frontend-validation-v2',status:'PASS',industry_categories:categories.length,dividends,languages:['en','vi'],public_consumer_rejected:true,mode:'saved real API contracts and server rendering',browser:'PENDING',mobile_visual_acceptance:'PENDING'};
writeFileSync(resolve(report),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));
