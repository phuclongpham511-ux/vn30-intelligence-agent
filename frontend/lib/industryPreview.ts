import type {BoardRow} from './quoteMap.ts';

/** Local synthetic evidence only. A future licensed taxonomy needs its own qualified receipt. */
export type IndustryPreview={kind:'synthetic';label:'DEMO';categories:Record<string,{code:string;name:string}>};
export function industryPreviewGroups(rows:BoardRow[],preview:IndustryPreview|undefined,enabled=false) {
  if(!enabled||preview?.kind!=='synthetic'||preview.label!=='DEMO'||rows.some(r=>!/^DEMO\d+$/.test(r.stock.symbol)))return null;
  const groups=new Map<string,{code:string;name:string;rows:BoardRow[]}>();
  for(const row of rows) {
    const category=preview.categories[row.stock.symbol];
    const code=category?.code&&category.name?category.code:'unclassified';
    if(!groups.has(code))groups.set(code,{code,name:code==='unclassified'?'Unclassified':category.name,rows:[]});
    groups.get(code)!.rows.push(row);
  }
  return [...groups.values()]; // Keep the existing numeric row order within every group.
}
