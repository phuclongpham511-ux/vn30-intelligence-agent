// Offline private API fixture validation. Does not start Next or a browser.
import {readFileSync,writeFileSync,readdirSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {financialEngineData} from '../lib/financial-engine-data.ts';
const [directory,report]=process.argv.slice(2);
if(!directory||!report)throw Error('Usage: node scripts/validate-financial-activation.mjs PRIVATE_RESPONSES REPORT_JSON');
const rows=[];
for(const name of readdirSync(directory).filter(n=>/^[A-Z0-9]+-(annual|quarterly|ttm)\.json$/.test(n))){
 const data=JSON.parse(readFileSync(join(directory,name),'utf8'));
 const parsed=financialEngineData(data,data.ticker,data.period_type,true,true,true);
 let publicRejected=false;
 try{financialEngineData(data,data.ticker,data.period_type,true);}catch{publicRejected=true;}
 if(!publicRejected)throw Error('Private observations entered public consumer');
 rows.push({ticker:parsed.ticker,frequency:parsed.period_type,verification:parsed.verification.statuses,
  public_consumer_rejected:true,panels:parsed.research_panels.filter(p=>['cashflow','profitability','liquidity','bank_funding'].includes(p.key)).map(p=>({key:p.key,status:p.status,points:p.rows.reduce((n,r)=>n+Object.values(r.values).filter(v=>v!==null).length,0)}))});
}
if(!rows.length)throw Error('No saved private response fixtures');
writeFileSync(resolve(report),JSON.stringify({contract:'real-financial-frontend-validation-v1',status:'PASS',mode:'offline frontend data contracts',browser_status:'PENDING',projections:rows},null,2)+'\n');
console.log(JSON.stringify({status:'PASS',projections:rows.length,browser_status:'PENDING'}));
