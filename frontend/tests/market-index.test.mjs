import test from 'node:test';
import assert from 'node:assert/strict';
import {indexMovement,indexAggregate,indexDate} from '../lib/marketIndex.ts';
test('index movement maps only observed direction, preserving unavailable and zero',()=>{
 assert.equal(indexMovement({change:5.88}).mascot,'marketUp');
 assert.equal(indexMovement({change:-3}).mascot,'marketDown');
 assert.equal(indexMovement({change:0}).mascot,'marketNeutral');
 assert.equal(indexMovement({change:null}).mascot,'marketUncertain');
 assert.equal(indexMovement(null).label,'Direction unavailable');
});

test('index aggregate formatting preserves null and real zero with explicit units',()=>{
 assert.equal(indexAggregate(null,'VND'),'Unavailable');
 assert.equal(indexAggregate(undefined,'shares'),'Unavailable');
 assert.equal(indexAggregate(0,'VND'),'0 VND');
 assert.match(indexAggregate(18715110854170,'VND'),/18.72tn VND/);
 assert.equal(indexDate('2026-10-06'),'06 Oct 2026');
});
