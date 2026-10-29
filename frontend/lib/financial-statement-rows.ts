import type {FinancialStatementPeriod} from './types.ts';

/** Source parent codes only; never invent a hierarchy from code prefixes. */
export function statementHierarchy(periods:FinancialStatementPeriod[],collapsed:ReadonlySet<string>){
 const lines=[...new Map(periods.flatMap(p=>p.items.map(line=>[line.code,line] as const))).values()];
 const lookup=new Map(lines.map(line=>[line.code.toLowerCase(),line]));
 return lines.map(line=>{
  const ancestors:string[]=[];let parent=line.semantic_status==='conflicted'?undefined:line.parent?.toLowerCase();const visited=new Set([line.code.toLowerCase()]);
  while(parent&&lookup.has(parent)&&lookup.get(parent)!.semantic_status!=='conflicted'&&!visited.has(parent)){
   visited.add(parent);const ancestor=lookup.get(parent)!;ancestors.push(ancestor.code);parent=ancestor.parent?.toLowerCase();
  }
  // Cyclic source relationships do not create an expandable display tree.
  const cycle=!!parent&&visited.has(parent);
  return {line,depth:cycle?0:Math.min(ancestors.length,8),hidden:!cycle&&ancestors.some(code=>collapsed.has(code)),
   expandable:!cycle&&line.semantic_status!=='conflicted'&&lines.some(child=>child.semantic_status!=='conflicted'&&child.parent?.toLowerCase()===line.code.toLowerCase()&&child.code!==line.code)};
 });
}
