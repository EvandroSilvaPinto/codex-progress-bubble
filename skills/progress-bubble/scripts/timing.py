"""Shared, honest presentation of an agent-supplied estimated finish time."""
from datetime import datetime
import math
from i18n import t


def eta_text(data, now=None, language=None):
    language = language or data.get("language")
    status = data.get('status')
    if status == 'Concluído':
        return t('Finalizado',language)
    if status in ('Falha','Interrompido','Aguardando informação'):
        return t('Previsão suspensa',language)
    if not data.get('eta_at'):
        return t('Estimando término',language)
    try:
        finish = datetime.fromisoformat(data['eta_at'])
        remaining = (finish-(now or datetime.now().astimezone())).total_seconds()
    except (TypeError,ValueError):
        return t('Estimando término',language)
    if remaining <= 0:
        return t('Recalculando previsão',language)
    if remaining < 60:
        return t('Menos de 1 min',language)
    minutes = max(1,math.ceil(remaining/60))
    return t('Faltam cerca de {minutes} min',language,minutes=minutes)
