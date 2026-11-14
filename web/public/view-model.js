export function parseLink(fragment) {
  const match=fragment.match(/^#([a-f0-9]{32})\.([A-Za-z0-9_-]{43})$/);
  return match?{id:match[1],token:match[2]}:null;
}
export function resolveLink(fragment,storage) {
  if(fragment)return parseLink(fragment);
  try{const saved=JSON.parse(storage.getItem('pb-session')||'null');return saved?parseLink('#'+saved.id+'.'+saved.token):null;}
  catch{return null;}
}
export function estimated(d,now=Date.now()) {
  const actual=Math.max(0,Math.min(100,d.percent)),base=Math.max(0,Math.min(99,d.visual_base??actual));
  if(d.status==='Concluído')return 100;
  let value=Math.max(actual,base);
  const start=Date.parse(d.visual_started_at),duration=Date.parse(d.eta_at)-start;
  if(d.status==='Em andamento'&&Number.isFinite(duration)&&duration>0){
    const ceiling=Math.max(base,95);
    value=Math.max(actual,Math.min(ceiling,base+(ceiling-base)*.9*Math.max(0,now-start)/duration));
  }
  return value;
}
export function remaining(d,now=Date.now(),lang='en') {
  const pt=lang==='pt',left=Date.parse(d.eta_at)-now;
  if(d.status==='Concluído')return pt?'Finalizado':'Finished';
  if(d.status!=='Em andamento')return pt?'Previsão suspensa':'Estimate paused';
  if(!Number.isFinite(left))return pt?'Estimando término':'Estimating time remaining';
  if(left<=0)return pt?'Recalculando previsão':'Recalculating estimate';
  if(left<60000)return pt?'Menos de 1 min':'Less than 1 min';
  return pt?`Faltam cerca de ${Math.ceil(left/60000)} min`:`About ${Math.ceil(left/60000)} min left`;
}
export function startPolling({load,onData,onError,document,setTimeout=globalThis.setTimeout,clearTimeout=globalThis.clearTimeout}) {
  let stopped=false,timer,controller,generation=0;
  async function refresh(){
    if(stopped||document.hidden)return;
    const current=++generation;controller=new AbortController();
    try{const data=await load(controller.signal);if(current===generation&&!stopped&&!document.hidden)onData(data);}
    catch(error){if(current===generation&&!stopped&&!document.hidden&&error.name!=='AbortError')onError(error);}
    finally{if(current===generation&&!stopped&&!document.hidden)timer=setTimeout(refresh,15000);}
  }
  function visibility(){clearTimeout(timer);generation++;controller?.abort();if(!document.hidden)refresh();}
  document.addEventListener('visibilitychange',visibility);refresh();
  return ()=>{stopped=true;generation++;clearTimeout(timer);controller?.abort();document.removeEventListener('visibilitychange',visibility);};
}

export function publisherStale(snapshot,now=Date.now()) {
 return snapshot.payload.status!=='Concluído'&&now-snapshot.updated_at>90000;
}
