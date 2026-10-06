import test from 'node:test';
import assert from 'node:assert/strict';
import {indexMovement} from '../lib/marketIndex.ts';
test('index movement maps only observed direction, preserving unavailable and zero',()=>{
 assert.equal(indexMovement({change:5.88}).mascot,'marketUp');
 assert.equal(indexMovement({change:-3}).mascot,'marketDown');
 assert.equal(indexMovement({change:0}).mascot,'marketNeutral');
 assert.equal(indexMovement({change:null}).mascot,'marketUncertain');
 assert.equal(indexMovement(null).label,'Direction unavailable');
});
