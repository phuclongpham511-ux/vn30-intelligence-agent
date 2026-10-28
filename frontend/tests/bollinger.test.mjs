import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {technicalSeries} from '../lib/chart-data.ts';
import {LanguageContext,localeTools} from '../lib/i18n.ts';

const require=createRequire(import.meta.url);
function component(path, replacements={}) {
  const code=transformSync(readFileSync(new URL(path,import.meta.url),'utf8'),{filename:path,
    module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
  const exports={};
  new Function('require','exports',code)(name=>replacements[name]||require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
  return exports.default;
}
const render=(Component,props,language='en')=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,
  {value:{...localeTools(language),setLanguage(){}}},React.createElement(Component,props)));
const bar={date:'2001-03-01',open:100,high:104,low:98,close:102,volume:300,ma20:101,ma50:100,rsi14:55,
  bb50_upper:104,bb50_lower:96,bb50_std:2};

test('BB series render backend values, preserve zero and omit unavailable observations',()=>{
  const rows=[{...bar,date:'2001-02-28',bb50_upper:null,bb50_lower:null,ma50:null},bar];
  const data=technicalSeries(rows,'up','down');
  assert.deepEqual(data.bb50_upper,[{time:bar.date,value:104}]);
  assert.deepEqual(data.bb50_lower,[{time:bar.date,value:96}]);
  assert.deepEqual(data.ma50,[{time:bar.date,value:100}]);
  assert.equal(technicalSeries([{...bar,bb50_lower:0}],'up','down').bb50_lower[0].value,0);
  assert.deepEqual(technicalSeries([{...bar,bb50_upper:null,bb50_lower:null}],'up','down').bb50_upper,[]);
});

test('legend only exposes BB when enabled, with EN/VI labels and missing dashes',()=>{
  const Legend=component('../app/components/stock/TechnicalLegend.tsx');
  assert.doesNotMatch(render(Legend,{bar,bb:false}),/Upper BB/);
  const en=render(Legend,{bar,bb:true});
  assert.match(en,/Upper BB/); assert.match(en,/Lower BB/); assert.match(en,/SMA50 \/ Middle BB/);
  assert.match(en,/>104</); assert.match(en,/>96</);
  const vi=render(Legend,{bar,bb:true},'vi');
  assert.match(vi,/Biên BB trên/); assert.match(vi,/Biên BB dưới/);
  const empty=render(Legend,{bar:{...bar,bb50_upper:null,bb50_lower:null,ma50:null},bb:true});
  assert.match(empty,/—/); assert.doesNotMatch(empty,/>0</);
});

test('toolbar has one accessible optional BB control alongside existing indicators',()=>{
  const Toolbar=component('../app/components/stock/TechnicalToolbar.tsx',{'../ui/button':{
    Button:({variant,size,...props})=>React.createElement('button',props)}});
  const props={range:'6M',onRange(){},reset(){},onIndicators(){},
    indicators:{MA20:true,MA50:false,BB:false,Volume:true,RSI:true}};
  const off=render(Toolbar,props);
  assert.match(off,/Bollinger Bands \(50, 2\)/);
  assert.match(off,/<input[^>]+type="checkbox"[^>]*\/>BB/);
  const on=render(Toolbar,{...props,indicators:{...props.indicators,BB:true}});
  assert.match(on,/<input[^>]+checked=""[^>]*\/>BB/);
  assert.match(render(Toolbar,props,'vi'),/Dải Bollinger \(50, 2\)/);
});
