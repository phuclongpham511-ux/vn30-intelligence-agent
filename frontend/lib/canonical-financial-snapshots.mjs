import {readFileSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {createHash} from 'node:crypto';

const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
export function readSnapshotConfiguration(cwd=process.cwd()){
 const path=resolve(cwd,'../data/personal-financial-runtime.json');
 if(!existsSync(path))return null;
 const config=JSON.parse(readFileSync(path,'utf8'));
 if(config.contract!=='canonical-local-financial-v1'||!['VN30','VN100'].includes(config.scope)||!Array.isArray(config.tickers)||config.tickers.length!==(config.scope==='VN30'?30:100)||new Set(config.tickers).size!==config.tickers.length||config.tickers.some(t=>!/^[A-Z0-9]{1,20}$/.test(t))||!/^([a-f0-9]{64})$/.test(config.index_sha256))throw Error('Invalid financial release configuration');
 const bytes=readFileSync(config.index);
 if(digest(bytes)!==config.index_sha256)throw Error('Financial index changed');
 const index=JSON.parse(bytes);
 if(index.contract!=='private-financial-projection-v1'||!index.engine_commit||!index.generated_at)throw Error('Invalid financial projection index');
 return {config,index,root:dirname(config.index)};
}
export function canonicalFinancialEnabled(){
 return process.env.WOOFI_PERSONAL_BOUNDARY==='canonical-loopback-custom-server-v1'&&process.env.WOOFI_DEPLOYMENT_KIND==='canonical-personal'&&process.env.APP_ENV==='production';
}
export function readCanonicalFinancial(ticker,frequency,evidence){
 if(!canonicalFinancialEnabled())throw Error('Canonical private boundary unavailable');
 const selected=readSnapshotConfiguration();
 if(!selected||!selected.config.tickers.includes(ticker))return null;
 const item=selected.index.items[`${ticker}:${frequency}:${evidence}`];
 if(!item)return null;
 if(!/^[a-f0-9]{64}\.json$/.test(item.file))throw Error('Invalid financial artifact');
 const bytes=readFileSync(resolve(selected.root,item.file));
 if(bytes.length>20000000||digest(bytes)!==item.sha256)throw Error('Financial projection changed');
 const data=JSON.parse(bytes);
 if(data.ticker!==ticker||data.period_type!==frequency||data.is_fixture!==false||!['personal_research','internal_research'].includes(data.display_scope)||!Array.isArray(data.rows))throw Error('Financial projection ownership mismatch');
 return bytes.toString('utf8');
}
export function readCanonicalFinancialRatios(ticker,frequency){
 if(!canonicalFinancialEnabled())throw Error('Canonical private boundary unavailable');
 const selected=readSnapshotConfiguration();
 if(!selected||!selected.config.tickers.includes(ticker)||!['annual','quarterly'].includes(frequency))return null;
 const {ratio_index:ratioPath,ratio_index_sha256:expected}=selected.config;
 if(typeof ratioPath!=='string'||!/^([a-f0-9]{64})$/.test(expected||''))return null;
 const bytes=readFileSync(ratioPath);
 if(digest(bytes)!==expected)throw Error('Financial ratio index changed');
 const index=JSON.parse(bytes);
 if(index.contract!=='vnstock-ratio-projection-v1'||index.scope!=='VN100'||index.source!=='KBS'||
   !Array.isArray(index.tickers)||index.tickers.length!==100||new Set(index.tickers).size!==100||
   index.tickers.some(value=>!/^[A-Z0-9]{1,20}$/.test(value))||
   selected.config.tickers.some(value=>!index.tickers.includes(value))||!index.items||typeof index.items!=='object')
  throw Error('Invalid financial ratio index');
 const item=index.items[`${ticker}:${frequency}`];
 if(!item)return null;
 if(!/^[a-f0-9]{64}\.json$/.test(item.file)||!/^[a-f0-9]{64}$/.test(item.sha256))throw Error('Invalid financial ratio artifact');
 const artifact=readFileSync(resolve(dirname(ratioPath),'responses',item.file));
 if(artifact.length>2000000||digest(artifact)!==item.sha256)throw Error('Financial ratio artifact changed');
 const data=JSON.parse(artifact);
 if(data.contract!=='vnstock-ratio-response-v1'||data.ticker!==ticker||data.frequency!==frequency||
   data.source!=='KBS'||!Array.isArray(data.periods)||data.periods.length>8||!Array.isArray(data.rows)||data.rows.length>100)
  throw Error('Financial ratio ownership mismatch');
 return artifact.toString('utf8');
}
