import {canonicalFinancialEnabled} from './canonical-financial-snapshots.mjs';
// Server-only configuration; never imported by client components.
export function personalRuntimeEnabled(){
 return canonicalFinancialEnabled()||process.env.WOOFI_PERSONAL_RESEARCH==='1'&&process.env.WOOFI_PERSONAL_BOUNDARY==='loopback-custom-server-v1'&&process.env.WOOFI_DEPLOYMENT_KIND==='personal-development';
}
export function personalBackend(){
 if(!personalRuntimeEnabled())throw Error('Personal research disabled');
 const base=process.env.WOOFI_PERSONAL_BACKEND;
 if(base!=='http://127.0.0.1:8432')throw Error('Invalid personal research backend');
 return base;
}
