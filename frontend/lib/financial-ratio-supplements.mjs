// Values are already calculated by the deterministic Python Engine.
// Provider identifiers are not aliases: total_assets, for example, means growth at KBS.
export function financialRatioSupplements(engine,ticker,frequency){
 if(!engine||engine.ticker!==ticker||engine.period_type!==frequency||engine.is_fixture!==false||!['personal_research','internal_research'].includes(engine.display_scope))return [];
 return [['free_cash_flow','Free cash flow','VND'],['cash_conversion','Operating cash flow / profit','×']].map(([key,label,unit])=>{
  const values={},evidence={};
  for(const row of engine.rows||[]){
   const calculation=row.calculations?.[key],value=row[key];
   const usable=!row.is_fixture&&calculation?.reason===null&&calculation.inputs?.length>0&&typeof value==='number'&&Number.isFinite(value);
   values[row.period]=usable?value:null;
   if(usable)evidence[row.period]=calculation;
  }
  return {metric_id:'woofi_'+key,label,unit,origin:'Woofi',values,evidence};
 }).filter(row=>Object.values(row.values).some(value=>value!==null));
}
