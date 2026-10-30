import test from 'node:test';
import assert from 'node:assert/strict';
import {industryPreviewGroups} from '../lib/industryPreview.ts';
const rows=['DEMO03','DEMO01','DEMO02'].map(symbol=>({stock:{symbol}}));
const preview={kind:'synthetic',label:'DEMO',categories:{DEMO01:{code:'demo-a',name:'DEMO Products'},DEMO03:{code:'demo-a',name:'DEMO Products'}}};
test('industry fixture retains sorted stock rows and exact counts, including Unclassified',()=>{
  const groups=industryPreviewGroups(rows,preview,true);
  assert.equal(groups[0].name,'DEMO Products');assert.equal(groups[0].rows.length,2);
  assert.deepEqual(groups[0].rows.map(r=>r.stock.symbol),['DEMO03','DEMO01']);
  assert.equal(groups[1].name,'Unclassified');assert.equal(groups[1].rows[0],rows[2]);
});
test('production, real-company assignments and unlabeled evidence cannot activate grouping',()=>{
  assert.equal(industryPreviewGroups(rows,preview),null);
  assert.equal(industryPreviewGroups([{stock:{symbol:'ACB'}}],preview,true),null);
  assert.equal(industryPreviewGroups(rows,{...preview,label:''},true),null);
  assert.equal(industryPreviewGroups(rows,{...preview,kind:'provider'},true),null);
  assert.equal(industryPreviewGroups(rows,undefined,true),null);
});
