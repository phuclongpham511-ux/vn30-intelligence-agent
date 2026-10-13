export type Stock = { id: number; symbol: string; company_name: string | null; display_name_en?: string | null; exchange: string | null; sector?: string | null };
export type Security = { symbol: string; exchange: string; company_name?: string | null; display_name_en?: string | null; source?: string; instrument_type?: string; last_synced_at?: string };
export type Bar = { date: string; open: number; high: number; low: number; close: number; volume: number; source: string };
export type Market = { ticker: string; as_of: string | null; close: number | null; source: string } & Record<string, string | number | null>;
export type Fundamental = { period: string | null; source: string } & Record<string, string | number | null>;
export type News = { id: string; published_at: string; title: string; summary_or_content: string | null; source: string; is_fixture: boolean; url: string | null };
export type Overview = { stock: Stock; history: Bar[]; market: Market; fundamentals: Fundamental; news: News[] };
export type TechnicalBar = Bar & { ticker: string; currency: string; ma20: number | null; ma50: number | null; rsi14: number | null;
  bb50_upper: number | null; bb50_lower: number | null; bb50_std: number | null };
export type FundamentalPeriod = {
  ticker: string; period: string; source: string; currency: string;
  revenue: number | null; net_profit: number | null; gross_margin: number | null; net_margin: number | null; roe: number | null;
  revenue_growth_yoy: number | null; net_profit_growth_yoy: number | null;
  gross_margin_change: number | null; net_margin_change: number | null; roe_change: number | null;
};
export type FinancialChange = {metric:'revenue'|'net_profit';current_period:string;prior_period:string;current:number;previous:number|null;absolute_change:number|null;growth_yoy:number|null};
export type FundamentalResearch = {
  ticker:string; source:string; currency:'VND'; period_type:'annual'; rows:FundamentalPeriod[]; changes:FinancialChange[];
  sector:string|null; industry:string|null; financial_identity_guard:boolean;
  publication_date:null; consolidation:null; read_at:string; read_kind:'provider_or_process_cache';
  available_period_types:string[]; available_statements:string[];
};
