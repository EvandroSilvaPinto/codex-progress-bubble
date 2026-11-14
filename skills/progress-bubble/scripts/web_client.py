"""Optional HTTPS session sharing. Writer capabilities never enter deliverables."""
import time
from http.client import HTTPException
import hashlib
import json
import os
from pathlib import Path
import secrets
from urllib import request as urllib_request, error as urllib_error
from urllib.parse import urlsplit
import uuid
import re
from contextlib import contextmanager
from colors import config_path

FIELDS=('title','message','status','percent','language','eta_at','visual_base','visual_started_at')


class WebError(Exception):
    def __init__(self,message='unavailable',status=None):
        super().__init__(message)
        self.status=status


class NoRedirect(urllib_request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def validate_endpoint(value):
    parsed=urlsplit(value)
    if (parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in ('','/')):
        raise ValueError('Use an HTTPS service origin without credentials, path, query or fragment')
    return value.rstrip('/')


def secret_path(state_path):
    identity=hashlib.sha256(str(Path(state_path).resolve()).encode('utf-8')).hexdigest()
    return config_path().parent/'sessions'/(identity+'.web-secret.json')


def save_secret(path,value):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        descriptor=os.open(str(temporary),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(descriptor,'w',encoding='utf-8') as stream:
            json.dump(value,stream,ensure_ascii=False)
        os.replace(temporary,path)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_secret(path):
    if not path.exists():
        return None
    try:
        value=json.loads(path.read_text(encoding='utf-8'))
        if (not isinstance(value,dict) or not re.fullmatch(r'[a-f0-9]{32}',value.get('id',''))
                or any(not re.fullmatch(r'[A-Za-z0-9_-]{43}',value.get(key,'')) for key in ('read_token','write_token'))):
            raise ValueError()
        validate_endpoint(value['endpoint'])
        return value
    except (OSError,ValueError,KeyError,TypeError):
        raise WebError('Private sharing settings could not be read') from None


@contextmanager
def task_lock(path,wait=False):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    descriptor=os.open(str(path.with_suffix('.lock')),os.O_RDWR|os.O_CREAT,0o600)
    with os.fdopen(descriptor,'r+b') as stream:
        deadline=time.monotonic()+25
        while True:
            try:
                if os.name=='nt':
                    import msvcrt
                    if stream.seek(0,2)==0:stream.write(b'0');stream.flush()
                    stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except OSError:
                if not wait or time.monotonic()>=deadline:raise
                time.sleep(.02)
        yield


def request(endpoint,method,path,body=None,key=None):
    endpoint=validate_endpoint(endpoint)
    headers={'User-Agent':'ProgressBubble/1.0','Content-Type':'application/json','Accept':'application/json'}
    if key:
        headers['Authorization']='Bearer '+key
    req=urllib_request.Request(endpoint+path,data=json.dumps(body).encode('utf-8') if body is not None else None,
                               headers=headers,method=method)
    try:
        with urllib_request.build_opener(NoRedirect()).open(req,timeout=8) as response:
            raw=response.read(32769)
            if len(raw)>32768:
                raise WebError()
            value=json.loads(raw.decode('utf-8')) if raw else {}
            if not isinstance(value,dict):raise WebError('Invalid sharing response')
            return value
    except urllib_error.HTTPError as error:
        raise WebError('Web service rejected the request',error.code) from None
    except (urllib_error.URLError,OSError,ValueError,HTTPException):
        raise WebError('Web synchronization unavailable') from None


def public_info(record,error=None):
    return dict(url=record['endpoint']+'/#'+record['id']+'.'+record['read_token'] if record.get('created') else None,
                error=error,id=record['id'],expires_at=record.get('expires_at'))


def sync_task(snapshot,state_path,endpoint=None,create=False):
    if not create and not secret_path(state_path).exists():
        return None
    try:
        with task_lock(secret_path(state_path),wait=True):
            return _sync_task(snapshot,state_path,endpoint,create)
    except OSError:
        return dict(url=None,error='Web sync busy; retry on the next update')


def _sync_task(snapshot,state_path,endpoint=None,create=False):
    path=secret_path(state_path)
    record=None
    try:
        record=load_secret(path)
        if record is None:
            if not create:
                return None
            record=dict(endpoint=validate_endpoint(endpoint),id=format(int(time.time()*1000),'012x')+secrets.token_hex(10),
                        read_token=secrets.token_urlsafe(32),write_token=secrets.token_urlsafe(32),created=False,version=1)
            save_secret(path,record)
        elif endpoint and validate_endpoint(endpoint)!=record['endpoint']:
            raise WebError('This task is already bound to another web service')
        if record.get('revocation_pending'):
            return _stop_sharing(state_path)
        if snapshot.get('delivery_id') and Path(state_path).is_file():
            latest=json.loads(Path(state_path).read_text(encoding='utf-8'))
            if latest.get('delivery_id')!=snapshot['delivery_id']:snapshot=latest
        payload={key:snapshot.get(key) for key in FIELDS if key in snapshot}
        payload['title']=str(snapshot.get('title',''))[:120]
        payload['message']=str(snapshot.get('message',''))[:280]
        if record['created']:
            result=request(record['endpoint'],'PATCH','/api/sessions/'+record['id'],
                           dict(version=record['version'],payload=payload),record['write_token'])
        else:
            result=request(record['endpoint'],'POST','/api/sessions',
                           {key:record[key] for key in ('id','read_token','write_token')}|dict(payload=payload))
        if not isinstance(result,dict):raise WebError('Invalid sharing response')
        if not record['created'] and result.get('payload') is not None and result['payload']!=payload:
            record.update(created=True,version=result['version']);save_secret(path,record)
            result=request(record['endpoint'],'PATCH','/api/sessions/'+record['id'],dict(version=record['version'],payload=payload),record['write_token'])
        if not isinstance(result,dict) or result.get('id')!=record['id'] or not isinstance(result.get('version'),int):
            raise WebError('Invalid sharing response')
        record.update(created=True,version=result['version'],expires_at=result.get('expires_at'))
        save_secret(path,record)
        return public_info(record)
    except (WebError,OSError,ValueError,KeyError,TypeError) as error:
        if record and isinstance(error,WebError) and error.status==409 and record.get('created'):
            try:
                latest=request(record['endpoint'],'GET','/api/sessions/'+record['id'],key=record['read_token'])
                record['version']=latest['version'];save_secret(path,record)
            except (WebError,OSError,KeyError):
                pass
        message='Web sync failed; local progress is preserved'
        return public_info(record,message) if record else dict(url=None,error=message)


def stop_sharing(state_path):
    try:
        with task_lock(secret_path(state_path),wait=True):
            return _stop_sharing(state_path)
    except OSError:
        return dict(url=None,error='Revocation pending; reconnect and retry')


def _stop_sharing(state_path):
    path=secret_path(state_path)
    try:
        record=load_secret(path)
        if record is None:
            return dict(url=None,error=None)
        record['revocation_pending']=True
        save_secret(path,record)
        try:
            request(record['endpoint'],'DELETE','/api/sessions/'+record['id'],key=record['write_token'])
        except WebError as error:
            if error.status not in (404,410):
                raise
        path.unlink()
        return dict(url=None,error=None)
    except (WebError,OSError,KeyError):
        return dict(url=None,error='Revocation pending; reconnect and retry')
