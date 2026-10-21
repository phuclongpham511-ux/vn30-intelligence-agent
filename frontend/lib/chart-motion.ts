import {useEffect, useState} from 'react';

/** Keep Recharts animations off during SSR and whenever reduced motion is preferred. */
export function useChartMotion(){
  const [reduced,setReduced]=useState(true);
  useEffect(()=>{
    const media=window.matchMedia('(prefers-reduced-motion: reduce)');
    const update=()=>setReduced(media.matches);
    update();
    media.addEventListener?.('change',update);
    return ()=>media.removeEventListener?.('change',update);
  },[]);
  return !reduced;
}
