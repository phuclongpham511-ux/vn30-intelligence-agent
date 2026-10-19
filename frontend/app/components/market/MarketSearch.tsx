"use client";
import {createContext,useContext,useState,type ReactNode} from 'react';
const Context=createContext({query:'',setQuery:(_query:string)=>{}});
/** Shares the existing metadata search; quote fetching remains in LivePrices. */
export function MarketSearchProvider({children}:{children:ReactNode}){const [query,setQuery]=useState('');return <Context.Provider value={{query,setQuery}}>{children}</Context.Provider>;}
export const useMarketSearch=()=>useContext(Context);
