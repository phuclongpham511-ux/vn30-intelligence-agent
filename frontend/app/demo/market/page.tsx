import {notFound} from 'next/navigation';
import MarketDemo from './MarketDemo';

export default function DemoPage() {
  if(process.env.NEXT_PUBLIC_WOOFI_VALIDATION!=='replay')notFound();
  return <MarketDemo/>;
}
