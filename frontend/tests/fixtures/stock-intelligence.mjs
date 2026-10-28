// Synthetic research contracts only; not live source evidence.
export const at='2026-10-18T05:00:00Z';
export const source={source_id:'publisher',name:'Publisher',enabled:true,status:'healthy',last_success_at:at};
export const forum={...source,source_id:'f319_public',name:'F319'};
export const article={id:'article',title:'AAA reports earnings',url:'https://publisher.example/a',source_name:'Publisher',published_at:'2026-10-18T02:00:00Z',first_seen_at:'2026-10-18T03:00:00Z',last_seen_at:'2026-10-18T04:00:00Z',tickers:['AAA'],topics:['Earnings'],sectors:[]};
export const news={id:'news:story',entity_id:'story',kind:'news',revision:'v1',revision_members:{article:'v1'},title:article.title,url:article.url,occurred_at:article.first_seen_at,evidence:[article]};
export const thread={id:'thread',title:'AAA original discussion',url:'https://newf319.com/threads/a.123/',published_at:'2026-10-18T02:30:00Z',first_seen_at:'2026-10-18T03:30:00Z',last_seen_at:at,tickers:['AAA'],source_id:'f319_public',replies:null,views:0,is_fixture:true,excerpt:'Original unverified discussion'};
export const discussion={id:'community:thread',entity_id:'thread',kind:'community',revision:'c1',title:thread.title,url:thread.url,occurred_at:thread.published_at,evidence:thread};
const page=items=>({items,has_more:false,truncated:false});
export const packet=(newsRows=[news],communityRows=[discussion])=>({as_of:at,offset:0,page_size:12,stocks:[{symbol:'AAA',status:'ready',news:page(newsRows),community:page(communityRows),technical:null}],news_sources:[source],community_sources:[forum]});
export const saved=()=>({symbols:['AAA','BBB'],seen:{},communitySeen:{}});
