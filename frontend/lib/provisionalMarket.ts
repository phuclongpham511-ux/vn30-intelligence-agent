import type {BoardIdentity,BoardRow,BoardSort} from './quoteMap.ts';
import type {LiveBatch} from './live-market.ts';

type Metric={field:string;value:number;raw_value:string|number;normalized_decimal:string;unit:string;multiplier:1;qualification:'PROVISIONAL_INTERNAL';unit_authority:'owner_engineering_convention'};
type Receipt={source:string;source_timestamp:string|null;fetched_at:string;record_sha256:string;document_sha256:string;raw_record:Record<string,unknown>};
export type ProvisionalMarket={contract:'ssi-provisional-market-v1';qualification:'PROVISIONAL_INTERNAL';convention_version:'woofi-owner-market-conventions-v1';public_display_eligible:false;certification:'NOT_SSI_CERTIFIED';display_rights:'NOT_QUALIFIED_FOR_PUBLIC';
  key:{symbol:string;exchange:string;trading_date:string};
  bands:{floor:Metric;reference:Metric;ceiling:Metric;source_timestamp:string|null;fetched_at:string;effectiveness:'trading_day_provisional'};
  matched:{volume:Metric;value:Metric;source_timestamp:string|null;fetched_at:string;cumulative:true;aggregation:'snapshot_do_not_sum';trade_inclusion:'provisional_unverified';scope:'instrument_trading_day_not_all_market'};
  freshness:{status:'fresh'|'stale'|'unverified';evaluated_at:string;max_source_age_seconds:120};
  validation:Record<'identity'|'date_alignment'|'bands'|'totals'|'plausibility','PASS'>;
  receipts:{master:Receipt;summary:Receipt;identity:Receipt}};

export function provisionalSsiEnabled(env:{nodeEnv?:string;flag?:string;validation?:string}) {
  return env.nodeEnv==='development'&&env.flag==='1'&&env.validation==='replay';
}
export function provisionalSsiLocalHost(host:string|null,forwardedHost:string|null) {
  return !forwardedHost&&!!host&&/^(?:127\.0\.0\.1|localhost|\[::1\])(?::\d{1,5})?$/.test(host);
}
const day=(v:Date)=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).format(v);
const time=(v:unknown)=>typeof v==='string'&&/(?:Z|[+-]\d\d:\d\d)$/.test(v)?Date.parse(v):NaN;
const hash=(v:unknown)=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const numeric=(v:unknown):v is number=>typeof v==='number'&&Number.isFinite(v)&&v>=0&&v<=Number.MAX_SAFE_INTEGER;
const decimal=(v:string)=>v.length<=128&&/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(v);

/** Transport checks only; Python owns normalization and exact plausibility math. */
export function provisionalMarketRecord(input:unknown,stock:BoardIdentity,now:Date):ProvisionalMarket|null {
  try {
    const p=input as ProvisionalMarket;
    if(!Number.isFinite(now.getTime())||!p||p.contract!=='ssi-provisional-market-v1'||p.qualification!=='PROVISIONAL_INTERNAL'||
      p.convention_version!=='woofi-owner-market-conventions-v1'||p.public_display_eligible!==false||p.certification!=='NOT_SSI_CERTIFIED'||p.display_rights!=='NOT_QUALIFIED_FOR_PUBLIC'||
      !/^[A-Z0-9]{1,20}$/.test(p.key.symbol)||p.key.symbol!==stock.symbol||p.key.exchange!==stock.exchange||!['HOSE','HNX','UPCOM'].includes(p.key.exchange)||
      !/^\d{4}-\d{2}-\d{2}$/.test(p.key.trading_date)||new Date(p.key.trading_date).toISOString().slice(0,10)!==p.key.trading_date||p.key.trading_date>day(now)||
      p.bands.effectiveness!=='trading_day_provisional'||p.matched.cumulative!==true||p.matched.aggregation!=='snapshot_do_not_sum'||p.matched.trade_inclusion!=='provisional_unverified'||
      p.matched.scope!=='instrument_trading_day_not_all_market'||p.freshness.max_source_age_seconds!==120||!['fresh','stale','unverified'].includes(p.freshness.status)||
      !['identity','date_alignment','bands','totals','plausibility'].every(k=>p.validation[k as keyof typeof p.validation]==='PASS'))return null;
    for(const [metric,unit,field,raw] of [
      [p.bands.floor,'VND/share','floor',p.receipts.master.raw_record.floor],
      [p.bands.reference,'VND/share','refPrice',p.receipts.master.raw_record.refPrice],
      [p.bands.ceiling,'VND/share','ceiling',p.receipts.master.raw_record.ceiling],
      [p.matched.volume,'shares','totalMatch',p.receipts.summary.raw_record.totalMatch],
      [p.matched.value,'VND','totalMatchValue',p.receipts.summary.raw_record.totalMatchValue],
    ] as const) {
      if(!metric||!numeric(metric.value)||metric.unit!==unit||metric.field!==field||metric.multiplier!==1||metric.qualification!=='PROVISIONAL_INTERNAL'||metric.unit_authority!=='owner_engineering_convention'||
        !['string','number'].includes(typeof metric.raw_value)||typeof metric.raw_value==='string'&&!decimal(metric.raw_value)||
        typeof metric.normalized_decimal!=='string'||!decimal(metric.normalized_decimal)||
        metric.raw_value!==raw||Number(raw)!==metric.value||Number(metric.normalized_decimal)!==metric.value)return null;
    }
    if(p.bands.floor.value<=0||p.bands.floor.value>p.bands.reference.value||p.bands.reference.value>p.bands.ceiling.value||!Number.isSafeInteger(p.matched.volume.value))return null;
    if((p.matched.volume.value===0)!==(p.matched.value.value===0))return null;
    for(const r of [p.receipts.master.raw_record,p.receipts.summary.raw_record])if('currency' in r&&r.currency!=='VND')return null;
    for(const [r,keys,allowed] of [[p.receipts.master.raw_record,['price_unit','priceUnit'],['VND','VND/share']],[p.receipts.summary.raw_record,['volume_unit','volumeUnit'],['shares']],[p.receipts.summary.raw_record,['value_unit','valueUnit'],['VND']]] as const)
      if(keys.some(k=>k in r&&!(allowed as readonly unknown[]).includes(r[k])))return null;
    for(const name of ['master','summary','identity'] as const) {
      const r=p.receipts[name];
      if(!hash(r.record_sha256)||!hash(r.document_sha256)||r.raw_record.symbol!==p.key.symbol||
        r.source!==`SSI:FastConnect:v3:${name==='master'?'MasterData':name==='summary'?'SecuritiesSummary':'SecuritiesInfo'}`||
        !Number.isFinite(time(r.fetched_at))||time(r.fetched_at)>now.getTime()||
        r.source_timestamp!==null&&(!Number.isFinite(time(r.source_timestamp))||time(r.source_timestamp)>time(r.fetched_at)))return null;
      if(['board','exchange'].some(k=>k in r.raw_record&&r.raw_record[k]!==p.key.exchange))return null;
      if(name!=='identity'&&(r.raw_record.tradingDate!==p.key.trading_date.replaceAll('-','/')||day(new Date(r.fetched_at))<p.key.trading_date||r.source_timestamp!==null&&day(new Date(r.source_timestamp))!==p.key.trading_date))return null;
    }
    if(p.receipts.identity.raw_record.stockType!=='Stock'||!['board','exchange'].some(k=>p.receipts.identity.raw_record[k]===p.key.exchange)||
      !['board','exchange'].some(k=>p.receipts.master.raw_record[k]===p.key.exchange)||
      p.bands.fetched_at!==p.receipts.master.fetched_at||p.bands.source_timestamp!==p.receipts.master.source_timestamp||
      p.matched.fetched_at!==p.receipts.summary.fetched_at||p.matched.source_timestamp!==p.receipts.summary.source_timestamp)return null;
    return p;
  } catch {return null;}
}

export function provisionalFreshness(p:ProvisionalMarket,now:Date):'fresh'|'stale'|'unverified' {
  if(p.key.trading_date!==day(now))return 'stale';
  if(!p.matched.source_timestamp)return 'unverified';
  return now.getTime()-time(p.matched.source_timestamp)>120000?'stale':'fresh';
}

/** Not imported by acquisition; only the internal route supplies these receipts. */
export function provisionalBoardRecords(input:unknown[]|undefined,stocks:BoardIdentity[],data:LiveBatch|null,now:Date,enabled:boolean) {
  const records=new Map<string,ProvisionalMarket>();
  if(!enabled||!Array.isArray(input)||input.length>50||!Number.isFinite(now.getTime()))return records;
  for(const raw of input) {
    const record=inputRecord(raw);const stock=stocks.find(s=>s.symbol===record?.key?.symbol);
    const p=stock?provisionalMarketRecord(raw,stock,now):null;
    if(!p||records.has(p.key.symbol))return new Map<string,ProvisionalMarket>();
    const quote=data?.items[p.key.symbol]?.snapshot;
    if(quote&&(quote.ticker!==p.key.symbol||quote.trading_date!==p.key.trading_date||quote.price_unit!=='VND'||quote.reference_price!==p.bands.reference.value))return new Map<string,ProvisionalMarket>();
    records.set(p.key.symbol,p);
  }
  if(new Set([...records.values()].map(p=>p.key.trading_date)).size>1)return new Map<string,ProvisionalMarket>();
  return records;
}
const inputRecord=(raw:unknown)=>raw as Partial<ProvisionalMarket>|null;

export function sortProvisionalRows(rows:BoardRow[],records:Map<string,ProvisionalMarket>,sort:BoardSort) {
  if(!records.size||(sort!=='volume'&&sort!=='value'))return rows;
  return [...rows].sort((a,b)=>{
    const av=records.get(a.stock.symbol)?.matched[sort].value,bv=records.get(b.stock.symbol)?.matched[sort].value;
    return av===undefined?(bv===undefined?a.stock.symbol.localeCompare(b.stock.symbol):1):bv===undefined?-1:bv-av||a.stock.symbol.localeCompare(b.stock.symbol);
  });
}
