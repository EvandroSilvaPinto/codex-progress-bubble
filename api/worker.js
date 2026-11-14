import {DAY,HOUR,ID,TOKEN,failure,hash,snapshot,publicSession,expiry} from './model.js';
import * as store from './store.js';

const freshID=(id,now)=>typeof id==='string'&&ID.test(id)&&Math.abs(now-parseInt(id.slice(0,12),16))<300000;
const headers={'Content-Security-Policy':"default-src 'none'; frame-ancestors 'none'",'Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff',
  'Content-Type':'application/json; charset=utf-8','Cross-Origin-Resource-Policy':'same-origin'};
const reply=(value,status=200)=>new Response(status===204?null:JSON.stringify(value),{status,headers});
async function body(request) {
  if(!request.headers.get('Content-Type')?.toLowerCase().startsWith('application/json')) failure(415,'JSON required');
  if(Number(request.headers.get('Content-Length'))>8192) failure(413,'Payload too large');
  const reader=request.body?.getReader();if(!reader) failure(400,'Missing payload');
  const chunks=[];let size=0;
  while(true){const part=await reader.read();if(part.done)break;size+=part.value.length;
    if(size>8192){await reader.cancel();failure(413,'Payload too large');}chunks.push(part.value);}
  const bytes=new Uint8Array(size);let offset=0;for(const part of chunks){bytes.set(part,offset);offset+=part.length;}
  let value;
  try{value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));}catch{failure(400,'Invalid JSON');}
  if(!value||typeof value!=='object'||Array.isArray(value)) failure(400,'JSON object required');
  return value;
}
async function authorize(request,row,role,now) {
  const key=request.headers.get('Authorization')?.replace(/^Bearer /,'');
  if(!row||!TOKEN.test(key??'')||await hash(key)!==row[role+'_hash']) failure(404,'Session unavailable');
  if(row.revoked||row.expires_at<=now) failure(410,'Session expired or revoked');
}
async function createSession(request,env,now,url) {
  if(!env.CREATE_LIMITER||!(await env.CREATE_LIMITER.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'})).success)
    failure(429,'Creation limit reached');
  const value=await body(request);now=Date.now();
  if(typeof value.id!=='string'||!ID.test(value.id)||[value.read_token,value.write_token].some(key=>typeof key!=='string'||!TOKEN.test(key))||value.read_token===value.write_token)
    failure(400,'Invalid capabilities');
  const payload=snapshot(value.payload),read_hash=await hash(value.read_token),write_hash=await hash(value.write_token);
  let row=await store.find(env.DB,value.id),created=false;
  if(!row){
    if(!freshID(value.id,now))failure(410,'Creation identity expired; check your system clock');
    const done=payload.status==='Concluído';
    const candidate={id:value.id,read_hash,write_hash,payload:JSON.stringify(payload),
      hard_expires_at:now+DAY,expires_at:now+(done?HOUR:DAY),completed_at:done?now:null};
    created=await store.create(env.DB,candidate,now);row=await store.find(env.DB,value.id);
    if(!row) failure(429,'Active session limit reached');
  }
  if(row.read_hash!==read_hash||row.write_hash!==write_hash) failure(404,'Session unavailable');
  if(row.expires_at<=now||row.revoked) failure(410,'Session expired or revoked');
  return reply({...publicSession(row),viewer_url:url.origin+'/#'+row.id+'.'+value.read_token},created?201:200);
}
async function api(request,env) {
  const url=new URL(request.url);let now=Date.now();
  if(request.headers.get('Origin')&&request.headers.get('Origin')!==url.origin) failure(403,'Origin denied');
  if(env.REQUEST_LIMITER&&!(await env.REQUEST_LIMITER.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'})).success)
    failure(429,'Request limit reached');
  if(url.pathname==='/api/health'&&request.method==='GET') return reply({ok:true});
  if(url.pathname==='/api/sessions'&&request.method==='POST') return createSession(request,env,now,url);
  const match=url.pathname.match(/^\/api\/sessions\/([a-f0-9]{32})$/);
  if(!match) failure(404,'Not found');
  if(!['GET','PATCH','DELETE'].includes(request.method)) failure(405,'Method not allowed');
  const row=await store.find(env.DB,match[1]);
  if(!row&&request.method==='DELETE'){
    const key=request.headers.get('Authorization')?.replace(/^Bearer /,'');
    if(!freshID(match[1],now)||!TOKEN.test(key??''))failure(404,'Session unavailable');
    if(!(await env.CREATE_LIMITER.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'})).success)failure(429,'Creation limit reached');
    const canceled=await store.cancel(env.DB,match[1],await hash(key),now);
    if(canceled.meta.changes!==1)failure(404,'Session unavailable');return reply(null,204);
  }
  await authorize(request,row,request.method==='GET'?'read':'write',now);
  if(request.method==='GET') return reply(publicSession(row));
  if(request.method==='DELETE'){await store.revoke(env.DB,row.id,now);return reply(null,204);}
  const value=await body(request),payload=snapshot(value.payload);now=Date.now();
  if(!Number.isSafeInteger(value.version)||value.version<1) failure(400,'Version required');
  if(value.version!==row.version)failure(409,'Stale update');
  if(row.completed_at!==null&&payload.status!=='Concluído') failure(409,'Completed session cannot resume');
  const times=expiry(row,payload,now);
  if(!await store.update(env.DB,row.id,row.version,payload,times,now)) failure(409,'Stale update');
  return reply(publicSession(await store.find(env.DB,row.id)));
}
export default {
  async fetch(request,env) {
    if(!new URL(request.url).pathname.startsWith('/api/')) return env.ASSETS.fetch(request);
    try{return await api(request,env);}catch(error){return reply({error:error.code?error.message:'Temporarily unavailable'},error.code||503);}
  },
  async scheduled(_event,env){await store.cleanup(env.DB,Date.now());}
};
