"""Shared, honest presentation of an agent-supplied estimated finish time."""
from datetime import datetime
import math


def eta_text(data, now=None):
    status = data.get('status')
    if status == 'Concluído':
        return 'Finalizado'
    if status in ('Falha','Interrompido','Aguardando informação'):
        return 'Previsão suspensa'
    if not data.get('eta_at'):
        return 'Estimando término'
    try:
        finish = datetime.fromisoformat(data['eta_at'])
        remaining = (finish-(now or datetime.now().astimezone())).total_seconds()
    except (TypeError,ValueError):
        return 'Estimando término'
    if remaining <= 0:
        return 'Recalculando previsão'
    if remaining < 60:
        return 'Menos de 1 min'
    minutes = max(1,math.ceil(remaining/60))
    return f'Faltam cerca de {minutes} min'
