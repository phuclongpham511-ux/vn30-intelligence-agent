import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
import {actionDate,actionTerm,trustedAction} from '../lib/stock-detail.ts';

// Actual Python adapter -> existing in-memory repository -> current GET response shape.
// No fixture output is copied from the implementation; the renderer consumes its real output.
const root=new URL('../../',import.meta.url);
const python=fileURLToPath(new URL(process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python',root));
const script=`
import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, SQLModel, create_engine
from src.corporate_actions.repository import CorporateActionRepository
from src.corporate_actions.storage import CorporateActionRecord
from src.providers.vnstock.corporate_actions import normalize_event
from routers.stocks import stock_corporate_actions
def deny_network(*args, **kwargs):
    raise AssertionError('Offline pilot forbids network connections')
socket.socket.connect = socket.socket.connect_ex = deny_network
fixtures=json.loads(Path('tests/fixtures/vnstock_corporate_actions_v1.json').read_text(encoding='utf-8'))
engine=create_engine('sqlite://')
SQLModel.metadata.create_all(engine,tables=[CorporateActionRecord.__table__])
with Session(engine) as session:
    repo=CorporateActionRepository(session)
    for row in fixtures['records']:
        if row['case'] not in ('cash','stock','bonus','rights','missing_cash_zero','missing_cash_amount','missing_ratio'):continue
        notice=normalize_event(row['raw'],requested_symbol=row['requested_symbol'],amount_unit=row['amount_unit'],ratio_basis=row['ratio_basis'],semantics_reference=fixtures['semantics_reference'])
        repo.ingest(notice,received_at=datetime(2026,10,1,tzinfo=timezone.utc))
    pages=[stock_corporate_actions(symbol=s,limit=50,session=session) for s in ('ABC','XYZ')]
    print(json.dumps(jsonable_encoder(pages),ensure_ascii=False))
assert 'vnstock' not in sys.modules, 'External SDK must not be imported'
engine.dispose()
`;
const result=spawnSync(python,['-B','-X','utf8','-c',script],{cwd:fileURLToPath(root),encoding:'utf8',timeout:30000});
assert.equal(result.status,0,result.error?.message||result.stderr);
const pages=JSON.parse(result.stdout);
const require=createRequire(import.meta.url);
const component={};
const compiled=transformSync(readFileSync(new URL('../app/components/stock/StockActions.tsx',import.meta.url),'utf8'),{filename:'StockActions.tsx',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
new Function('require','exports',compiled)(name=>name==='./useStockRead'?{useStockRead:()=>{throw Error('No HTTP allowed')}}:name==='../ui/button'?{Button:({variant,...props})=>React.createElement('button',props)}:require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),component);

test('actual offline notices satisfy StockActions shape and fixture trust gates',()=>{
  const rows=pages.flatMap(page=>page.items);
  assert.deepEqual(new Set(rows.map(row=>row.action_type)),new Set(['cash_dividend','stock_dividend','bonus_shares','rights_offering']));
  for(const page of pages) {
    assert.equal(page.coverage,'INCOMPLETE');
    assert.equal(page.has_more,false);
    for(const row of page.items) {
      assert.equal(row.symbol,page.ticker);
      assert.equal(row.is_fixture,true);assert.equal(row.verified,false);assert.equal(row.withdrawn,false);
      assert.equal(trustedAction(row),false);
      assert.equal(actionDate(row,'record_date'),null);
      assert.equal(actionTerm(row,'cash_vnd_per_share'),null);
      assert.equal(actionTerm(row,'new_shares_per_old'),null);
      assert.equal(JSON.parse(row.evidence_text).mapping_contract,'vnstock-vci-events-offline-v1');
    }
  }
});

test('current EN/VI renderer accepts adapter output while retaining evidence and DEMO disclosure',()=>{
  for(const language of ['en','vi']) for(const page of pages) {
    const html=renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:{...localeTools(language),setLanguage(){}}},React.createElement(component.StockActionsView,{ticker:page.ticker,data:page,retry(){}})));
    assert.equal((html.match(/data-action-observation=/g)||[]).length,page.items.length);
    assert.match(html,/DEMO/);assert.match(html,/vnstock:VCI:events/);
    assert.match(html,/vnstock-vci-events-offline-v1/);
    assert.doesNotMatch(html,/1,500 VND|1\.500 VND|Source-marked verified/);
  }
});
