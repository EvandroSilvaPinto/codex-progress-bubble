"""Portuguese/English interface selected from the operating system language."""
import ctypes
from functools import lru_cache
import locale
import os

EN = {
    'Voltar':'Back',
    'Copiar link':'Copy link',

    'Celular':'Mobile', 'Acompanhar em outro dispositivo':'Follow on another device',
    'Compartilhar acompanhamento':'Share progress',
    'Enviar somente título, mensagem e progresso para gerar um link temporário? Quem tiver o link poderá visualizar esta demanda.':
    'Send only the title, message and progress to create a temporary link? Anyone with the link can view this task.',
    'Serviço web ainda não configurado.':'Web service is not configured yet.',
    'Não foi possível sincronizar. O acompanhamento local continua disponível.':
    'Could not synchronize. Local progress remains available.',
    'ACOMPANHAMENTO':'PROGRESS', 'Acompanhamento da demanda':'Task progress',
    'Sua demanda':'Your task', 'Aguardando atualização':'Waiting for an update',
    'Em andamento':'In progress', 'Concluído':'Completed', 'Falha':'Failed',
    'Interrompido':'Stopped', 'Aguardando informação':'Waiting for information',
    'Cores':'Colors', 'Redefinir cores':'Reset colors', 'Tamanhos':'Sizes',
    'progresso estimado':'estimated progress', 'Progresso estimado':'Estimated progress',
    'Abrir conversa  ↗':'Open chat  ↗', 'Abrir detalhes  ↗':'Open details  ↗',
    'Abrir conversa ↗':'Open chat ↗', 'Acompanhamento e cores':'Card and colors',
    'Bolinha':'Bubble', 'Pequeno':'Small', 'Médio':'Medium', 'Grande':'Large',
    'Fundo':'Background', 'Texto':'Text', 'Progresso':'Progress',
    'Detalhes':'Details', 'Estados':'States', 'Cor: {label}':'Color: {label}',
    'Fundo — cartão e bolinha':'Background — card and bubble',
    'Texto — títulos, mensagens e percentual':'Text — titles, messages and percentage',
    'Progresso — barra e anel':'Progress — bar and ring',
    'Detalhes — links e tempo restante':'Details — links and time remaining',
    'Estados — conclusão, falha e espera':'States — completed, failed and waiting',
    'Finalizado':'Finished', 'Previsão suspensa':'Estimate paused',
    'Estimando término':'Estimating time remaining', 'Recalculando previsão':'Recalculating estimate',
    'Menos de 1 min':'Less than 1 min', 'Faltam cerca de {minutes} min':'About {minutes} min left',
    'Não foi possível salvar: {error}':'Could not save: {error}',
    'Não foi possível salvar as cores: {error}':'Could not save colors: {error}',
    'Contraste baixo':'Low contrast', 'Não foi possível salvar a cor':'Could not save color',
    'Cor aplicada. Algumas combinações podem ficar difíceis de ler.\nVocê pode ajustar Fundo, Texto, Progresso ou Detalhes.':
    'Color applied. Some combinations may be difficult to read.\nYou can adjust Background, Text, Progress or Details.',
}


def language_for(name):
    return 'pt' if (name or '').lower().replace('_','-').startswith(('pt-','pt.')) or (name or '').lower()=='pt' else 'en'


@lru_cache(maxsize=1)
def system_language():
    if os.name == 'nt':
        try:
            # Display language, rather than the regional date/number format.
            code = ctypes.WinDLL('kernel32').GetUserDefaultUILanguage()
            return language_for(locale.windows_locale.get(code))
        except (AttributeError, OSError):
            pass
    for key in ('LC_ALL','LC_MESSAGES','LANGUAGE','LANG'):
        if os.environ.get(key):
            return language_for(os.environ[key].split(':')[0])
    try:
        return language_for(locale.getlocale()[0])
    except (ValueError, TypeError):
        return 'en'


def t(text, language=None, **values):
    translated = EN.get(text,text) if (language or system_language())=='en' else text
    return translated.format(**values) if values else translated
