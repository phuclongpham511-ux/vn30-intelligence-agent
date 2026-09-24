import test from 'node:test';
import assert from 'node:assert/strict';
import { technicalSeries } from '../lib/chart-data.ts';
test('indicator adapters omit warm-up nulls and preserve true zero RSI', () => {
  const rows = [{date:'2025-01-01',open:1,high:1,low:1,close:1,volume:1,ma20:null,ma50:null,rsi14:null},
    {date:'2025-01-02',open:1,high:1,low:1,close:1,volume:1,ma20:1,ma50:null,rsi14:0}];
  const data=technicalSeries(rows,'up','down');
  assert.deepEqual(data.ma20,[{time:'2025-01-02',value:1}]);
  assert.deepEqual(data.ma50,[]);
  assert.deepEqual(data.rsi14,[{time:'2025-01-02',value:0}]);
});
