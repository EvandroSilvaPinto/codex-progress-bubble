import test from 'node:test';
import assert from 'node:assert/strict';
test('switching private links in one tab replaces data and copy target even with blocked storage',async()=>{
 const originals=new Map(),listeners={},elements=new Map(),copied=[];
 const set=(name,value)=>{originals.set(name,Object.getOwnPropertyDescriptor(globalThis,name));Object.defineProperty(globalThis,name,{configurable:true,value});};
 const element=id=>{if(!elements.has(id))elements.set(id,{hidden:false,textContent:'',setAttribute(){},classList:{toggle(){}},addEventListener(name,fn){this[name]=fn;}});return elements.get(id);};
 const a='a'.repeat(32),b='c'.repeat(32),token='b'.repeat(43);
 const location={origin:'https://progress.example',pathname:'/',search:'',hash:'#'+a+'.'+token};
 const doc={hidden:false,documentElement:{},getElementById:element,addEventListener(name,fn){listeners[name]=fn;},removeEventListener(name){delete listeners[name];}};
 set('document',doc);set('location',location);set('history',{replaceState(){location.hash='';}});
 set('navigator',{language:'en',clipboard:{async writeText(value){copied.push(value);}}});
 set('sessionStorage',undefined);Object.defineProperty(globalThis,'sessionStorage',{configurable:true,get(){throw new Error('storage denied');}});
 set('addEventListener',(name,fn)=>{listeners[name]=fn;});set('setInterval',()=>0);
 set('fetch',async url=>({ok:true,json:async()=>({payload:{title:url.endsWith(a)?'Task A':'Task B',status:'Em andamento',percent:10},expires_at:Date.now()+60000,updated_at:Date.now()})}));
 try{
  await import('../public/app.js?browser-test');await new Promise(resolve=>setImmediate(resolve));
  assert.equal(element('title').textContent,'Task A');assert.equal(location.hash,'');
  location.hash='#'+b+'.'+token;listeners.hashchange();await new Promise(resolve=>setImmediate(resolve));
  assert.equal(element('title').textContent,'Task B');assert.equal(location.hash,'');
  await element('copy').click();assert.equal(copied[0],location.origin+'/#'+b+'.'+token);
 }finally{doc.hidden=true;listeners.visibilitychange?.();for(const [name,descriptor] of originals){if(descriptor)Object.defineProperty(globalThis,name,descriptor);else delete globalThis[name];}}
});
