import test from 'node:test';
import assert from 'node:assert/strict';
import jsQR from 'jsqr';
import {parseLink,resolveLink,publisherStale,estimated,remaining,startPolling} from '../public/view-model.js';
import {matrixFor} from '../public/qr.js';

const id='a'.repeat(32),key='b'.repeat(43),url='https://progress.example/#'+id+'.'+key;
test('reader link parsing rejects other paths, malformed capabilities and extra segments',()=>{
  assert.deepEqual(parseLink(new URL(url).hash),{id,token:key});
  for(const value of ['', '#bad','#'+id+'.'+key+'.extra','#'+id+'.short']) assert.equal(parseLink(value),null);
});
test('visual estimate and time remaining preserve completion and cap',()=>{
  const start=Date.now(),payload={percent:10,status:'Em andamento',visual_base:10,
    visual_started_at:new Date(start).toISOString(),eta_at:new Date(start+600000).toISOString()};
  assert.equal(estimated(payload,start),10);
  assert.equal(estimated(payload,start+600000),86.5);
  assert.equal(estimated(payload,start+3600000),95);
  assert.equal(remaining(payload,start,'en'),'About 10 min left');
  assert.equal(estimated({...payload,status:'Concluído',percent:100},start),100);
});
test('generated QR independently decodes to the exact read-only link',()=>{
  const matrix=matrixFor(url),scale=6,size=(matrix.length+8)*scale;
  const rgba=new Uint8ClampedArray(size*size*4).fill(255);
  for(let y=0;y<matrix.length;y++)for(let x=0;x<matrix.length;x++)if(matrix[y][x])
    for(let dy=0;dy<scale;dy++)for(let dx=0;dx<scale;dx++){
      const pos=(((y+4)*scale+dy)*size+(x+4)*scale+dx)*4;rgba[pos]=rgba[pos+1]=rgba[pos+2]=0;
    }
  assert.equal(jsQR(rgba,size,size)?.data,url);
});
test('polling stops while hidden and resumes when visible',async()=>{
  let visibility,loads=0,scheduled=0;
  const document={hidden:false,addEventListener(_name,fn){visibility=fn;},removeEventListener(){}};
  const stop=startPolling({load:async()=>{loads++;return {};},onData(){},onError(){},document,
    setTimeout(){scheduled++;return 1;},clearTimeout(){}});
  await new Promise(resolve=>setImmediate(resolve));assert.equal(loads,1);assert.equal(scheduled,1);
  document.hidden=true;visibility();await new Promise(resolve=>setImmediate(resolve));assert.equal(loads,1);
  document.hidden=false;visibility();await new Promise(resolve=>setImmediate(resolve));assert.equal(loads,2);
  stop();visibility();assert.equal(loads,2);
});

 test('invalid explicit fragments never fall back to a previous private task',()=>{
  const storage={getItem:()=>JSON.stringify({id,token:key})};
  assert.equal(resolveLink('#invalid',storage),null);
  assert.deepEqual(resolveLink('',storage),{id,token:key});
  assert.deepEqual(resolveLink('#'+id+'.'+key,storage),{id,token:key});
 });

test('a reachable API does not imply a fresh publisher update',()=>{
 assert.equal(publisherStale({updated_at:1000,payload:{status:'Em andamento'}},92000),true);
 assert.equal(publisherStale({updated_at:91000,payload:{status:'Em andamento'}},92000),false);
 assert.equal(publisherStale({updated_at:1000,payload:{status:'Concluído'}},92000),false);
});
