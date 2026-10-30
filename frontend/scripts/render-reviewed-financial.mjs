// Offline source rendering of real reviewed evidence, not browser acceptance.
// No server, fetch, storage, financial calculation or diagnostic hook overrides.
import {readFileSync,writeFileSync,mkdirSync,existsSync,readdirSync} from 'node:fs';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
const frontend=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(join(frontend,'package.json'));
const React=require('react'),{renderToStaticMarkup}=require('react-dom/server');
const {transformSync}=require('next/dist/build/swc/index.js');
const {financialEngineData}=require(join(frontend,'lib/financial-engine-data.ts'));
const {LanguageContext,localeTools}=require(join(frontend,'lib/i18n.ts'));
const [input,destination,compiledStyles]=process.argv.slice(2);
if(!input||!destination||existsSync(destination))throw Error('Supply internal-display.json and a NEW output folder');
const raw=JSON.parse(readFileSync(input,'utf8'));
assert.ok(['internal_research','personal_research'].includes(raw.display_scope));assert.equal(raw.is_fixture,false);
const data=financialEngineData(raw,raw.ticker,raw.period_type,true,raw.display_scope==='internal_research',raw.display_scope==='personal_research');
const css=compiledStyles?readdirSync(compiledStyles,{recursive:true}).filter(file=>file.endsWith('.css')).map(file=>readFileSync(join(compiledStyles,file),'utf8')).join('\n'):'';
const cache=new Map();
function load(file){
 if(cache.has(file))return cache.get(file);
 const exports={};cache.set(file,exports);
 const code=transformSync(readFileSync(file,'utf8'),{filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 new Function('require','exports',code)(id=>{
  if(id.startsWith('@/lib/'))return require(join(frontend,'lib',id.slice(6)+'.ts'));
  if(id.startsWith('.')){
   const base=resolve(dirname(file),id);
   if(existsSync(base+'.tsx'))return load(base+'.tsx');
   if(existsSync(base+'.ts'))return require(base+'.ts');
  }
  return require(id);
 },exports);return exports;
}
const {FundamentalTrendsView}=load(join(frontend,'app/components/stock/FundamentalTrends.tsx'));
const Table=load(join(frontend,'app/components/stock/FinancialStatementTable.tsx')).default;
mkdirSync(destination,{recursive:true});
const results=[];
for(const language of ['en','vi']){
 const tools=localeTools(language),el=React.createElement;
 const html=renderToStaticMarkup(el(LanguageContext.Provider,{value:tools},el('main',{className:'stock-financial-research',style:{padding:24,maxWidth:1200,margin:'auto'}},
  el('h1',null,data.ticker+' · '+tools.t('Fundamental analysis')),
  el('p',null,data.source+' · '+data.rows.map(r=>r.period).join(' / ')+' · VND · '+tools.ui(data.consolidation==='consolidated'?'Consolidated statements':data.consolidation==='standalone'?'Standalone statements':'Unknown basis')),
  el('p',null,language==='vi'?'Bản dựng HTML ngoại tuyến để kiểm tra số liệu; chưa phải nghiệm thu trình duyệt.':'Offline HTML evidence snapshot; browser acceptance pending.'),
  el(FundamentalTrendsView,{data,loading:false,error:false,retry:()=>{},frequency:data.period_type}),
  ...Object.entries(data.statements).filter(([,s])=>s.periods.length).map(([kind,s])=>el('section',{key:kind},
   el(Table,{periods:s.periods,unit:'vnd',label:kind==='income'?'Income statement':'Balance sheet'}))),
  el('details',null,el('summary',null,tools.t('Statement provenance')),
   el('pre',{style:{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}},JSON.stringify(data.source_receipts,null,2))))));
 assert.ok(html.includes('data-financial-scope="'+raw.display_scope+'"'));
 for(const statement of Object.values(data.statements))for(const period of statement.periods)for(const line of period.items){
  if(line.value!==null)assert.ok(html.includes(tools.number(line.value,0)),`Missing rendered original field ${line.code}/${period.period}`);
 }
 const name=`reviewed-financial-${language}.html`;
 writeFileSync(join(destination,name),'<!doctype html><html lang="'+language+'"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Internal filing review</title><style>'+css+'</style><body>'+html+'</body></html>');
 results.push({language,source:data.source,ticker:data.ticker,fieldsRendered:Object.values(data.statements).reduce((n,s)=>n+s.periods.reduce((n,p)=>n+p.items.filter(i=>i.value!==null).length,0),0),file:name,browserAcceptance:'PENDING',synthetic:false});
}
writeFileSync(join(destination,'RESULTS.json'),JSON.stringify(results,null,2));
console.log(JSON.stringify(results,null,2));
