"""Time-based visual estimates, separate from progress reported by the agent."""
from datetime import datetime
import math

RATE = .9
LIMIT = 95


def displayed_progress(data, now=None):
    actual = max(0,min(100,int(data.get('percent',0))))
    if data.get('status') == 'Concluído':
        return 100
    base = max(0,min(99,float(data.get('visual_base',actual))))
    if data.get('status') != 'Em andamento':
        return max(actual,base)
    try:
        start = datetime.fromisoformat(data['visual_started_at'])
        finish = datetime.fromisoformat(data['eta_at'])
        duration = (finish-start).total_seconds()
        elapsed = max(0,((now or datetime.now().astimezone())-start).total_seconds())
        if duration <= 0 or not math.isfinite(duration):
            return max(actual,base)
        ceiling = max(base,LIMIT)
        return max(actual,min(ceiling,base+(ceiling-base)*RATE*elapsed/duration))
    except (KeyError,TypeError,ValueError):
        return max(actual,base)


def visual_state(previous, actual, status, eta_at, now):
    """Keep a saved anchor across refreshes and prevent jumps backwards on re-estimation."""
    old = displayed_progress(previous,now) if previous and previous.get('status')!='Concluído' else actual
    base = max(actual,old)
    if status == 'Concluído':
        return dict(visual_base=100,visual_started_at=None)
    same = (status=='Em andamento' and previous.get('status')==status
            and eta_at==previous.get('eta_at') and actual<=old
            and previous.get('visual_started_at'))
    if same:
        return {key:previous[key] for key in ('visual_base','visual_started_at')}
    return dict(visual_base=min(99,base),visual_started_at=now.isoformat() if eta_at else None)


def progress_script(data):
    """Mirror the estimate in standalone HTML, without changing the saved actual percent."""
    import json
    model = {key:data.get(key) for key in ('percent','status','eta_at','visual_base','visual_started_at')}
    return '''
const progressModel = MODEL;
function refreshProgress(){
  const d=progressModel, actual=Math.max(0,Math.min(100,d.percent));
  const base=Math.max(0,Math.min(99,d.visual_base??actual));
  let value=d.status==='Concluído'?100:Math.max(actual,base);
  if(d.status==='Em andamento'&&d.eta_at&&d.visual_started_at){
    const start=Date.parse(d.visual_started_at), duration=Date.parse(d.eta_at)-start;
    if(Number.isFinite(duration)&&duration>0){
      const ceiling=Math.max(base,95);
      value=Math.max(actual,Math.min(ceiling,base+(ceiling-base)*0.9*Math.max(0,Date.now()-start)/duration));
    }
  }
  document.querySelector('progress').value=value;
  document.getElementById('progress-value').textContent=Math.floor(value)+'%';
}
refreshProgress();setInterval(refreshProgress,500);
'''.replace('MODEL',json.dumps(model,ensure_ascii=True))
