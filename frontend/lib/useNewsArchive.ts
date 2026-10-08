"use client";
import {useEffect,useRef,useState} from "react";
import type {TopStoryData} from "@/app/components/news/TopStory";

type Page={items:TopStoryData[]; as_of:string; next_offset:number|null; has_more:boolean};
export function useNewsArchive(query:string|null,attempt:number) {
  const [page,setPage]=useState<Page|null>(null);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState(false);
  const more=useRef<()=>void>(()=>{});
  const saved=useRef<{query:string|null;page:Page|null}>({query:null,page:null});
  useEffect(()=>{
    const controller=new AbortController();
    let current=saved.current.query===query?saved.current.page:null;
    saved.current={query,page:current};
    let busy=false;
    setPage(current);setError(false);setLoading(false);
    if(query===null){more.current=()=>{};return()=>controller.abort();}
    const read=async(offset=0,asOf?:string):Promise<Page>=>{
      const params=new URLSearchParams(query);
      params.set('limit','12');params.set('offset',String(offset));
      if(asOf)params.set('as_of',asOf);
      const response=await fetch(`/api/news/feed/page?${params}`,{signal:controller.signal,cache:'no-store'});
      if(!response.ok)throw new Error('News unavailable');
      return response.json();
    };
    const load=async(append=false)=>{
      if(busy||controller.signal.aborted||append&&(!current?.has_more||current.next_offset===null))return;
      busy=true;setLoading(true);setError(false);
      try{
        let next:Page;
        if(append&&current){
          const added=await read(current.next_offset!,current.as_of);
          next={...added,items:[...current.items,...added.items]};
        }else{
          const visible=current?.items.length||12;
          next=await read();
          // Refresh only pages the user has already revealed.
          while(next.items.length<visible&&next.has_more&&next.next_offset!==null){
            const added=await read(next.next_offset,next.as_of);
            next={...added,items:[...next.items,...added.items]};
          }
        }
        if(!controller.signal.aborted){current=next;saved.current={query,page:next};setPage(next);}
      }catch{if(!controller.signal.aborted)setError(true);}
      finally{busy=false;if(!controller.signal.aborted)setLoading(false);}
    };
    more.current=()=>{void load(true);};
    void load();
    const timer=setInterval(()=>{void load();},60_000);
    return()=>{controller.abort();clearInterval(timer);};
  },[query,attempt]);
  return {page,loading,error,loadMore:()=>more.current()};
}
