import {headers} from 'next/headers';
import {notFound} from 'next/navigation';
import {provisionalSsiEnabled,provisionalSsiLocalHost} from '@/lib/provisionalMarket';
import InternalBoard from './InternalBoard';
import saved from './saved-acb.json';

export const dynamic='force-dynamic';
export default async function Page() {
  if(!provisionalSsiEnabled({nodeEnv:process.env.NODE_ENV,flag:process.env.NEXT_PUBLIC_WOOFI_SSI_PROVISIONAL,validation:process.env.NEXT_PUBLIC_WOOFI_VALIDATION}))notFound();
  const request=await headers();
  if(!provisionalSsiLocalHost(request.get('host'),request.get('x-forwarded-host'))||request.get('x-forwarded-for'))notFound();
  return <InternalBoard packet={saved} asOf={new Date().toISOString()}/>;
}
