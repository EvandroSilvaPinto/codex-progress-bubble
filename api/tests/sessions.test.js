import test from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import worker from '../worker.js';

function environment() {
  const sqlite = new DatabaseSync(':memory:');
  sqlite.exec(readFileSync(new URL('../migrations/0001.sql',import.meta.url),'utf8'));
  const DB={prepare(sql){let values=[];return {bind(...args){values=args;return this;},
    async first(){return sqlite.prepare(sql).get(...values)||null;},
    async run(){const r=sqlite.prepare(sql).run(...values);return {meta:{changes:Number(r.changes)}};},
    async all(){return {results:sqlite.prepare(sql).all(...values)};}};}};
  return {DB,CREATE_LIMITER:{limit:async()=>({success:true})},sqlite};
}
const token=()=>crypto.randomUUID().replaceAll('-','')+'abcDEF12345';
function task() {return {id:Date.now().toString(16).padStart(12,'0')+crypto.randomUUID().replaceAll('-','').slice(0,20),read_token:token(),write_token:token(),
  payload:{title:'Private task',message:'Working',status:'Em andamento',percent:10,language:'en'}};}
function call(env,method,path,body,key) {
  return worker.fetch(new Request('https://progress.example'+path,{method,
    headers:{'Content-Type':'application/json',...(key?{Authorization:'Bearer '+key}:{})},
    ...(body?{body:JSON.stringify(body)}:{})}),env,{});
}

test('isolates sessions and reader/writer roles without leaking credentials',async()=>{
  const env=environment(),a=task(),b=task();
  assert.equal((await call(env,'POST','/api/sessions',a)).status,201);
  await call(env,'POST','/api/sessions',b);
  const read=await call(env,'GET','/api/sessions/'+a.id,null,a.read_token);
  assert.equal(read.status,200);assert.equal(read.headers.get('Cache-Control'),'no-store');
  const snapshot=await read.json();assert.equal(snapshot.payload.title,'Private task');
  assert.ok(!JSON.stringify(snapshot).includes(a.write_token));
  for(const key of [b.read_token,b.write_token,a.write_token,'wrong'])
    assert.equal((await call(env,'GET','/api/sessions/'+a.id,null,key)).status,404);
  assert.equal((await call(env,'PATCH','/api/sessions/'+a.id,{version:1,payload:a.payload},a.read_token)).status,404);
  const row=env.sqlite.prepare('SELECT * FROM sessions WHERE id=?').get(a.id);
  assert.ok(!JSON.stringify(row).includes(a.read_token));assert.ok(!JSON.stringify(row).includes(a.write_token));
});

test('creation retries are idempotent; updates reject stale versions',async()=>{
  const env=environment(),a=task();await call(env,'POST','/api/sessions',a);
  const retry=await call(env,'POST','/api/sessions',a);assert.equal(retry.status,200);
  const updated=await call(env,'PATCH','/api/sessions/'+a.id,{version:1,payload:{...a.payload,percent:50}},a.write_token);
  assert.equal(updated.status,200);assert.equal((await updated.json()).version,2);
  assert.equal((await call(env,'PATCH','/api/sessions/'+a.id,{version:1,payload:a.payload},a.write_token)).status,409);
  assert.equal(env.sqlite.prepare('SELECT COUNT(*) AS n FROM sessions').get().n,1);
});

test('completion shortens fixed expiry; expired and revoked capabilities stop working',async()=>{
  const env=environment(),a=task();const created=await(await call(env,'POST','/api/sessions',a)).json();
  const done=await(await call(env,'PATCH','/api/sessions/'+a.id,{version:1,payload:{...a.payload,status:'Concluído',percent:100}},a.write_token)).json();
  assert.ok(done.expires_at<created.expires_at);assert.ok(done.expires_at<=Date.now()+3601000);
  assert.equal((await call(env,'PATCH','/api/sessions/'+a.id,{version:2,payload:a.payload},a.write_token)).status,409);
  env.sqlite.prepare('UPDATE sessions SET expires_at=0 WHERE id=?').run(a.id);
  assert.equal((await call(env,'GET','/api/sessions/'+a.id,null,a.read_token)).status,410);
  const b=task();await call(env,'POST','/api/sessions',b);
  assert.equal((await call(env,'DELETE','/api/sessions/'+b.id,null,b.read_token)).status,404);
  assert.equal((await call(env,'DELETE','/api/sessions/'+b.id,null,b.write_token)).status,204);
  assert.equal((await call(env,'GET','/api/sessions/'+b.id,null,b.read_token)).status,410);
});

test('validates states, limits creation and excludes local metadata',async()=>{
  const env=environment(),a=task();
  assert.equal((await call(env,'POST','/api/sessions',{...a,payload:{...a.payload,percent:100}})).status,400);
  assert.equal((await call(env,'POST','/api/sessions',{...a,payload:{...a.payload,title:'x'.repeat(121)}})).status,400);
  a.payload.html='C:/private/report.html';a.payload.conversation_app='private.exe';
  await call(env,'POST','/api/sessions',a);
  const read=await(await call(env,'GET','/api/sessions/'+a.id,null,a.read_token)).json();
  assert.equal(read.payload.html,undefined);assert.equal(read.payload.conversation_app,undefined);
  env.CREATE_LIMITER.limit=async()=>({success:false});
  assert.equal((await call(env,'POST','/api/sessions',task())).status,429);
});

test('rejects malformed, oversized and cross-origin requests without exposing server errors',async()=>{
  const env=environment();
  for(const raw of ['null','[]','"text"','{']) {
    const response=await worker.fetch(new Request('https://progress.example/api/sessions',{method:'POST',
      headers:{'Content-Type':'application/json'},body:raw}),env,{});
    assert.equal(response.status,400,raw);
  }
  const large=await worker.fetch(new Request('https://progress.example/api/sessions',{method:'POST',
    headers:{'Content-Type':'application/json'},body:'x'.repeat(8193)}),env,{});
  assert.equal(large.status,413);
  const cross=await worker.fetch(new Request('https://progress.example/api/sessions',{method:'POST',
    headers:{Origin:'https://untrusted.example','Content-Type':'application/json'},body:'{}'}),env,{});
  assert.equal(cross.status,403);
});

test('cleanup removes expired sessions; completed updates cannot prolong access',async()=>{
  const env=environment(),a=task();await call(env,'POST','/api/sessions',a);
  const completed={...a.payload,status:'Concluído',percent:100};
  const done=await(await call(env,'PATCH','/api/sessions/'+a.id,{version:1,payload:completed},a.write_token)).json();
  const again=await(await call(env,'PATCH','/api/sessions/'+a.id,{version:2,payload:completed},a.write_token)).json();
  assert.equal(done.expires_at,again.expires_at);
  env.sqlite.prepare('UPDATE sessions SET expires_at=0,created_at=0').run();
  await worker.scheduled({},env);
  assert.equal(env.sqlite.prepare('SELECT COUNT(*) AS n FROM sessions').get().n,0);
});

test('capability arrays cannot collapse reader and writer roles',async()=>{
 const env=environment(),a=task();a.write_token=[a.read_token];
 assert.equal((await call(env,'POST','/api/sessions',a)).status,400);
});
test('cleaned revoked identities cannot recreate the original reader link',async()=>{
 const env=environment(),a=task();await call(env,'POST','/api/sessions',a);
 await call(env,'DELETE','/api/sessions/'+a.id,null,a.write_token);await worker.scheduled({},env);
 assert.equal((await call(env,'POST','/api/sessions',{...a,write_token:token()})).status,404);
 const future=Date.now()+86400001,original=Date.now;Date.now=()=>future;
 try{await worker.scheduled({},env);assert.notEqual((await call(env,'POST','/api/sessions',{...a,write_token:token()})).status,201);}
 finally{Date.now=original;}
});
test('a guessed future version cannot race a completion into reopening',async()=>{
 const env=environment(),a=task();await call(env,'POST','/api/sessions',a);
 const prepare=env.DB.prepare;let intercepted=false;
 env.DB.prepare=sql=>{const statement=prepare(sql);
  if(sql.startsWith('UPDATE sessions SET payload')){
   const run=statement.run;statement.run=async()=>{
    if(!intercepted){intercepted=true;env.sqlite.prepare('UPDATE sessions SET version=2,completed_at=?,expires_at=? WHERE id=?').run(Date.now(),Date.now()+3600000,a.id);}
    return run();
   };
  }return statement;
 };
 assert.equal((await call(env,'PATCH','/api/sessions/'+a.id,{version:2,payload:a.payload},a.write_token)).status,409);
});

test('revocation before a delayed creation leaves an unclaimable tombstone',async()=>{
 const env=environment(),a=task();
 assert.equal((await call(env,'DELETE','/api/sessions/'+a.id,null,a.write_token)).status,204);
 assert.notEqual((await call(env,'POST','/api/sessions',a)).status,201);
 assert.notEqual((await call(env,'GET','/api/sessions/'+a.id,null,a.read_token)).status,200);
});

test('cancellation wins when a pending create inserts between lookup and tombstone',async()=>{
 const env=environment(),a=task(),prepare=env.DB.prepare;let raced=false;
 env.DB.prepare=sql=>{const statement=prepare(sql);if(sql.includes("VALUES (?,'',?,'{}'")){
  const run=statement.run;statement.run=async()=>{if(!raced){raced=true;await call({...env,DB:{prepare}},'POST','/api/sessions',a);}return run();};
 }return statement;};
 assert.equal((await call(env,'DELETE','/api/sessions/'+a.id,null,a.write_token)).status,204);
 assert.equal((await call(env,'GET','/api/sessions/'+a.id,null,a.read_token)).status,410);
});

test('active-session and general request caps fail closed',async()=>{
 const env=environment(),a=task();await call(env,'POST','/api/sessions',a);
 env.sqlite.exec(`WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<499)
 INSERT INTO sessions (id,read_hash,write_hash,payload,created_at,updated_at,expires_at,hard_expires_at)
 SELECT printf('%032x',n.x),s.read_hash,s.write_hash,s.payload,s.created_at,s.updated_at,s.expires_at,s.hard_expires_at FROM sessions s,n`);
 assert.equal((await call(env,'POST','/api/sessions',task())).status,429);
 env.REQUEST_LIMITER={limit:async()=>({success:false})};
 assert.equal((await call(env,'GET','/api/sessions/'+a.id,null,a.read_token)).status,429);
});
test('database-time admission rejects a create delayed beyond its identity window',async()=>{
 const env=environment(),a=task();
 env.sqlite.function('julianday',(_input)=>2440587.5+(Date.now()+3600000)/86400000);
 assert.notEqual((await call(env,'POST','/api/sessions',a)).status,201);
 assert.equal(env.sqlite.prepare('SELECT COUNT(*) AS n FROM sessions').get().n,0);
});
