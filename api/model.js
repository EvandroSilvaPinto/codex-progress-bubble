export const DAY=86400000, HOUR=3600000;
export const ID=/^[a-f0-9]{32}$/, TOKEN=/^[A-Za-z0-9_-]{43}$/;
export function failure(code,message) {throw Object.assign(new Error(message),{code});}
export async function hash(value) {
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value))),v=>v.toString(16).padStart(2,'0')).join('');
}
export function snapshot(value) {
  if(!value||typeof value!=='object'||Array.isArray(value)) failure(400,'Invalid task');
  const {title,message,status,percent}=value;
  const statuses=['Em andamento','Aguardando informação','Concluído','Interrompido','Falha'];
  if(typeof title!=='string'||!title.trim()||title.length>120||typeof message!=='string'||message.length>280
    ||!statuses.includes(status)||!Number.isInteger(percent)||percent<0||percent>100
    ||(status==='Concluído')!==(percent===100)) failure(400,'Invalid task fields');
  const result={title,message,status,percent,language:value.language==='pt'?'pt':'en'};
  for(const key of ['eta_at','visual_started_at']) {
    const field=value[key];
    if(field!=null&&(typeof field!=='string'||field.length>40||!Number.isFinite(Date.parse(field)))) failure(400,'Invalid estimate');
    result[key]=field??null;
  }
  const base=value.visual_base??percent;
  if(typeof base!=='number'||!Number.isFinite(base)||base<0||base>100||(base===100&&percent!==100)) failure(400,'Invalid visual estimate');
  result.visual_base=base;
  return result;
}
export function publicSession(row) {
  return {id:row.id,payload:JSON.parse(row.payload),version:row.version,expires_at:row.expires_at,updated_at:row.updated_at};
}
export function expiry(row,payload,now) {
  const completed=row.completed_at??(payload.status==='Concluído'?now:null);
  return {completed,expires:Math.min(row.expires_at,completed===null?row.hard_expires_at:completed+HOUR)};
}
