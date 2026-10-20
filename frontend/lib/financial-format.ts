/** A small nonzero amount must never be rendered as an apparent zero. */
export function formatFinancialAmount(value:number,divisor:number,digits:number,number:(value:number,digits?:number)=>string){
 const scaled=value/divisor,threshold=10**-digits;
 return scaled!==0&&Math.abs(scaled)<threshold
  ?(scaled>0?'<':'>−')+number(threshold,digits):number(scaled,digits);
}
