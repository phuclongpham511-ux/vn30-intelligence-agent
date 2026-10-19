"use client";
import {useEffect,useState,type ReactNode} from "react";
import {safeExternalUrl} from "@/lib/presentation";
import {ImageOff} from 'lucide-react';

export default function NewsThumbnail({images, wide=false, compact=false, revision, required=true, reserveSpace=false, children}: {images:(string|null|undefined)[]; wide?:boolean; compact?:boolean; revision?:string; required?:boolean; reserveSpace?:boolean; children?:(image:ReactNode)=>ReactNode}) {
  const [failed,setFailed]=useState<string[]>([]);
  const identity=images.join('|');
  useEffect(()=>setFailed([]),[identity,revision]);
  const image=images.map(value=>safeExternalUrl(value||null)).find(url=>url&&!failed.includes(url));
  const frame='news-thumbnail '+(wide?"aspect-video w-full overflow-hidden rounded bg-muted":compact?"h-16 w-20 shrink-0 overflow-hidden rounded bg-muted":"h-20 w-24 shrink-0 overflow-hidden rounded bg-muted sm:h-24 sm:w-36");
  if(!image)return !required&&children?children(reserveSpace?<div className={frame+' news-thumbnail-fallback'} data-thumbnail-status="unavailable" aria-hidden="true"><ImageOff size={20}/></div>:null):null;
  const thumbnail=<div className={frame} data-thumbnail-status="available">
    <img src={image} alt=""
      loading="lazy" referrerPolicy="no-referrer" width={288} height={192}
      onError={()=>setFailed(previous=>[...previous,image])}
      className="h-full w-full object-cover"/>
  </div>;
  return children?children(thumbnail):thumbnail;
}
