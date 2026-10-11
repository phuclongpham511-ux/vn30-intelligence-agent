// Refresh persisted read APIs; never schedules acquisition from the browser.
export function cacheRefresh(load:()=>void, visibility:Pick<Document,'visibilityState'|'addEventListener'|'removeEventListener'>=document, focus:Pick<Window,'addEventListener'|'removeEventListener'>=window, scheduler={set:(fn:()=>void)=>setInterval(fn,60000),clear:(id:ReturnType<typeof setInterval>)=>clearInterval(id)}) {
  const refresh=()=>{if(visibility.visibilityState==='visible')load();};
  const timer=scheduler.set(refresh);
  visibility.addEventListener('visibilitychange',refresh);focus.addEventListener('focus',refresh);
  return()=>{scheduler.clear(timer);visibility.removeEventListener('visibilitychange',refresh);focus.removeEventListener('focus',refresh);};
}
