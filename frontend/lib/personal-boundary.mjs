/** Socket peer + literal Host + same-origin browser policy. Forwarded headers
 * never authorize access. Reject DNS rebinding and foreign-site localhost reads. */
export function localResearchRequest(peer,headers,port=3431){
 if(![3431,3000].includes(port))return false;
 return peer==='127.0.0.1'&&headers.host===`127.0.0.1:${port}`&&
  (!headers.origin||headers.origin===`http://127.0.0.1:${port}`)&&
  (!headers['sec-fetch-site']||['same-origin','none'].includes(headers['sec-fetch-site']));
}
