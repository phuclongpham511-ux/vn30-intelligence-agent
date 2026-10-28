"use client";
import {useEffect,useState} from 'react';
import {equityPageUrl,loadEquityPage,type EquityQuery,type UniversePage} from './universe.ts';

// A changed query clears the visible page immediately; obsolete requests cannot win.
export function useEquityPage(options:EquityQuery,enabled=true,delay=0) {
  const url=enabled?equityPageUrl(options):'';
  const [attempt,setAttempt]=useState(0);
  const key=url+'|'+attempt;
  const [state,setState]=useState<{key:string;data:UniversePage|null;error:boolean}>({key:'',data:null,error:false});
  useEffect(()=>{
    const controller=new AbortController();
    if(!url)return;
    const timer=window.setTimeout(()=>{
      void loadEquityPage(url,controller.signal).then(data=>{
        if(!controller.signal.aborted)setState({key,data,error:false});
      }).catch(()=>{if(!controller.signal.aborted)setState({key,data:null,error:true});});
    },delay);
    return()=>{window.clearTimeout(timer);controller.abort();};
  },[url,key,delay]);
  const current=state.key===key?state:null;
  return {data:current?.data||null,error:!!current?.error,loading:enabled&&!current?.data&&!current?.error,refresh:()=>setAttempt(value=>value+1)};
}
