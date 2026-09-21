import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateCafe, filterCafes, readWorkspace } from './workspace.mjs';
const cafe={name:'Test Café',location:'https://example.com/map',open_time:'08:00',close_time:'17:00',coffee_rating:4,wifi_rating:3,power_rating:2};
test('normalize valid personal cafe',()=>{assert.equal(validateCafe({...cafe,name:' Test Café '}).name,'Test Café');});
test('reject unsafe links and invalid ratings/times',()=>{for(const patch of [{location:'javascript:alert(1)'},{location:'https://user:pass@example.com/'},{coffee_rating:8},{wifi_rating:NaN},{power_rating:1.5},{open_time:'25:00'},{name:''}])assert.throws(()=>validateCafe({...cafe,...patch}));});
test('recover safely from invalid storage and duplicate ids',()=>{assert.deepEqual(readWorkspace('{bad'),{cafes:[],saved:[]});const c={...cafe,id:'local-1'};const data=readWorkspace(JSON.stringify({cafes:[c,c,{...c,id:'local-2',location:'javascript:x'}],saved:['local-1',1,1,{},'local-2']}));assert.equal(data.cafes.length,1);assert.deepEqual(data.saved,['local-1',1]);});
test('combine query, minimum ratings and ranking',()=>{const rows=[{...cafe,name:'Alpha'},{...cafe,name:'Beta',wifi_rating:5,power_rating:4}];assert.equal(filterCafes(rows,{sort:'work'})[0].name,'Beta');assert.equal(filterCafes(rows,{q:' ALP ',wifi:3}).length,1);assert.equal(filterCafes(rows,{power:5}).length,0);});
