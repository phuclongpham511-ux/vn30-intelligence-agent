import {notFound} from 'next/navigation';
import FinancialValidation from './validation';
export default function Page(){
 if(process.env.NEXT_PUBLIC_WOOFI_VALIDATION!=='replay')notFound();
 return <FinancialValidation/>;
}
