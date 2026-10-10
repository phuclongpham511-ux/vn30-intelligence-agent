"use client";
import {useEffect,useState,type ReactNode} from "react";
import {safeExternalUrl} from "@/lib/presentation";

export default function NewsThumbnail({images, wide=false, compact=false, revision, children}: {images:(string|null|undefined)[]; wide?:boolean; compact?:boolean; revision?:string; children?:(image:ReactNode)=>ReactNode}) {
  const [failed,setFailed]=useState<string[]>([]);
  const identity=images.join('|');
  useEffect(()=>setFailed([]),[identity,revision]);
  const image=images.map(value=>safeExternalUrl(value||null)).find(url=>url&&!failed.includes(url));
  if(!image)return null;
  const thumbnail=<div className={wide?"aspect-video w-full overflow-hidden rounded bg-muted":compact?"h-16 w-20 shrink-0 overflow-hidden rounded bg-muted":"h-20 w-24 shrink-0 overflow-hidden rounded bg-muted sm:h-24 sm:w-36"}>
    <img src={image} alt=""
      loading="lazy" referrerPolicy="no-referrer" width={288} height={192}
      onError={()=>setFailed(previous=>[...previous,image])}
      className="h-full w-full object-cover"/>
  </div>;
  return children?children(thumbnail):thumbnail;
}
