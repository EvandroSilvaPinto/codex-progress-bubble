import {parseLink,resolveLink,publisherStale,estimated,remaining,startPolling} from './view-model.js';
import {paintQR} from './qr.js';

const pt=(navigator.language||'').toLowerCase().startsWith('pt'),lang=pt?'pt':'en';
const words=pt?{
  cloud:'Acompanhamento na nuvem',eyebrow:'SUA DEMANDA À VISTA',empty:'Abra seu link privado',
  help:'Sem cadastro. Cada link abre somente uma demanda.',loading:'Conectando ao acompanhamento…',
  synced:'Conectado ao acompanhamento',stale:'Sem atualizações recentes do agente. Exibindo o último progresso recebido.',offline:'Sem conexão. Exibindo a última atualização recebida.',
  expired:'Este acompanhamento expirou ou foi encerrado.',invalid:'Link inválido ou indisponível.',
  unavailable:'Serviço temporariamente indisponível. Tentaremos novamente.',estimated:'progresso estimado',
  qr:'Mostrar QR code',copy:'Copiar link privado',copied:'Link privado copiado.',copyFailed:'Não foi possível copiar o link.',
  share:'Continue em outro dispositivo',shareHelp:'Escaneie com o celular. Quem tiver o link poderá visualizar esta demanda até ele expirar.',
  close:'Fechar',notice:'Link privado por demanda · sem histórico permanente',
  until:'Disponível até',states:{'Em andamento':'Em andamento','Concluído':'Concluído','Falha':'Falha','Interrompido':'Interrompido','Aguardando informação':'Aguardando informação'}
}:{cloud:'Cloud tracking',eyebrow:'YOUR TASK, IN VIEW',empty:'Open your private task link',
  help:'No account needed. Each link opens just one task.',loading:'Connecting to your task…',synced:'Connected to your task',stale:'No recent updates from the agent. Showing the last received progress.',
  offline:'Offline. Showing the last received update.',expired:'This task link has expired or was closed.',invalid:'Invalid or unavailable link.',
  unavailable:'Temporarily unavailable. We will retry.',estimated:'estimated progress',qr:'Show QR code',copy:'Copy private link',
  copied:'Private link copied.',copyFailed:'Could not copy the link.',share:'Continue on another device',
  shareHelp:'Scan with your phone. Anyone with the link can view this task until it expires.',close:'Close',
  notice:'Private session links · no permanent task history',
  until:'Available until',states:{'Em andamento':'In progress','Concluído':'Completed','Falha':'Failed','Interrompido':'Stopped','Aguardando informação':'Waiting for information'}};
const $=id=>document.getElementById(id);
document.documentElement.lang=lang;
for(const [id,value] of Object.entries({cloud:words.cloud,eyebrow:words.eyebrow,title:words.empty,connection:words.help,
  estimated:words.estimated,'qr-button':words.qr,copy:words.copy,'share-title':words.share,'share-help':words.shareHelp,
  'close-qr':words.close,notice:words.notice})) $(id).textContent=value;
$('bar').setAttribute('aria-label',words.estimated);
$('qr').setAttribute('aria-label',pt?'QR code do link privado desta demanda':'QR code for this private task link');
let link=null,snapshot,stop=()=>{},autoQR=false;
function receiveLink(fragment){
  stop();snapshot=null;$('task').hidden=$('share').hidden=true;
  try{link=resolveLink(fragment,sessionStorage);}catch{link=parseLink(fragment);}
  if(fragment){
    try{history.replaceState(null,'',location.pathname+location.search);}catch{}
    try{if(link)sessionStorage.setItem('pb-session',JSON.stringify(link));else sessionStorage.removeItem('pb-session');}catch{}
  }
  autoQR=new URLSearchParams(location.search).get('qr')==='1';
  $('title').textContent=words.empty;$('message').textContent='';
  $('connection').textContent=fragment&&!link?words.invalid:words.help;
  if(link)connect();
}
const shareURL=()=>location.origin+'/#'+link.id+'.'+link.token;
function clearPrivate(message){
  stop();snapshot=null;link=null;
  try{sessionStorage.removeItem('pb-session');}catch{}
  $('title').textContent=words.empty;$('message').textContent='';$('task').hidden=$('share').hidden=true;
  $('qr').width=$('qr').height=0;$('connection').textContent=message;
}
function tick(){
  if(!snapshot)return;
  if(Date.now()>=snapshot.expires_at){clearPrivate(words.expired);return;}
  const value=estimated(snapshot.payload);$('bar').value=value;$('percent').textContent=Math.floor(value)+'%';
  $('eta').textContent=remaining(snapshot.payload,Date.now(),lang);
  if(publisherStale(snapshot)&&$('connection').textContent===words.synced)$('connection').textContent=words.stale;
}
function render(data){
  snapshot=data;$('task').hidden=false;$('title').textContent=data.payload.title;$('message').textContent=data.payload.message;
  $('state').textContent=(data.payload.status==='Concluído'?'✓ ':'● ')+words.states[data.payload.status];
  $('state').classList.toggle('done',data.payload.status==='Concluído');$('connection').textContent=publisherStale(data)?words.stale:words.synced;
  $('reported').textContent=(pt?'Informado pelo agente: ':'Reported by agent: ')+data.payload.percent+'%';
  $('expires').textContent=words.until+' '+new Intl.DateTimeFormat(navigator.language,{hour:'2-digit',minute:'2-digit'}).format(data.expires_at);
  tick();
}
function showQR(){if(!link||!snapshot)return;paintQR($('qr'),shareURL());$('share').hidden=false;}
$('qr-button').addEventListener('click',showQR);
$('close-qr').addEventListener('click',()=>{$('share').hidden=true;});
$('copy').addEventListener('click',async()=>{
  if(!link)return;try{await navigator.clipboard.writeText(shareURL());$('notice').textContent=words.copied;}
  catch{$('notice').textContent=words.copyFailed;}
});
function connect(){
  const target=link;
  $('connection').textContent=words.loading;
  stop=startPolling({document,load:async signal=>{
    const response=await fetch('/api/sessions/'+target.id,{headers:{Authorization:'Bearer '+target.token},cache:'no-store',signal});
    if(!response.ok)throw Object.assign(new Error('Request failed'),{status:response.status});return response.json();
  },onData:data=>{render(data);if(autoQR&&snapshot){autoQR=false;showQR();}},
  onError:error=>{
    if(error.status===410)clearPrivate(words.expired);
    else if(error.status===404||error.status===401)clearPrivate(words.invalid);
    else $('connection').textContent=snapshot?words.offline:words.unavailable;
  }});
}
addEventListener('hashchange',()=>receiveLink(location.hash));
receiveLink(location.hash);
setInterval(tick,500);
