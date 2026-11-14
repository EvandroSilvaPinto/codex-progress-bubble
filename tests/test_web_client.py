import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import threading
from unittest.mock import patch

SCRIPTS=Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'
sys.path.insert(0,str(SCRIPTS))
web=importlib.import_module('web_client')


class SharingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env=patch.dict(os.environ,APPDATA=self.tmp.name,XDG_CONFIG_HOME=self.tmp.name)
        self.env.start();self.addCleanup(self.env.stop)
        self.state=Path(self.tmp.name)/'demo.json'
        self.payload=dict(title='Task',message='Working',status='Em andamento',percent=10,
                          html='C:/private/path.html',conversation_app='private.exe',conversation_url='codex://private')

    def test_local_mode_never_contacts_the_network(self):
        with patch.object(web,'request') as call:
            self.assertIsNone(web.sync_task(self.payload,self.state))
            call.assert_not_called()

    def test_retry_reuses_private_capabilities_and_does_not_upload_local_metadata(self):
        calls=[]
        def response(endpoint,method,path,body=None,key=None):
            calls.append((method,path,body,key))
            if len(calls)==1:raise web.WebError('unavailable')
            return dict(id=body['id'],version=1,expires_at=9999999999999)
        with patch.object(web,'request',side_effect=response),contextlib.redirect_stdout(io.StringIO()) as output:
            first=web.sync_task(self.payload,self.state,'https://progress.example',True)
            second=web.sync_task(self.payload,self.state,'https://progress.example',True)
        self.assertTrue(first['error']);self.assertTrue(second['url'])
        self.assertEqual(calls[0][2]['write_token'],calls[1][2]['write_token'])
        self.assertEqual(calls[0][2]['id'],calls[1][2]['id'])
        self.assertNotIn('html',calls[1][2]['payload'])
        self.assertNotIn('conversation_app',calls[1][2]['payload'])
        self.assertNotIn('conversation_url',calls[1][2]['payload'])
        self.assertNotIn(calls[0][2]['write_token'],output.getvalue()+json.dumps(second))
        self.assertNotIn(calls[0][2]['write_token'],second['url'])
        secret=web.secret_path(self.state)
        self.assertTrue(secret.is_file())
        if os.name!='nt':self.assertEqual(secret.stat().st_mode&0o777,0o600)

    def test_invalid_endpoint_and_redirect_cannot_forward_credentials(self):
        for endpoint in ('http://example.com','https://user:pass@example.com','https://example.com/?secret=x'):
            with self.assertRaises(ValueError):web.validate_endpoint(endpoint)
        self.assertIsNone(web.NoRedirect().redirect_request(None,None,302,'',{},'https://evil.example'))

    def test_revocation_uses_writer_and_disables_future_sync(self):
        def response(endpoint,method,path,body=None,key=None):
            if method=='POST':return dict(id=body['id'],version=1,expires_at=9999999999999)
            self.assertEqual(method,'DELETE');self.assertEqual(len(key),43);return {}
        with patch.object(web,'request',side_effect=response):
            web.sync_task(self.payload,self.state,'https://progress.example',True)
            result=web.stop_sharing(self.state)
        self.assertFalse(result['error']);self.assertFalse(web.secret_path(self.state).exists())
        self.assertIsNone(web.sync_task(self.payload,self.state))

    def test_uncertain_creation_can_still_be_revoked(self):
        calls=[]
        def response(endpoint,method,path,body=None,key=None):
            calls.append(method)
            if method=='POST':raise web.WebError('response lost')
            return {}
        with patch.object(web,'request',side_effect=response):
            web.sync_task(self.payload,self.state,'https://progress.example',True)
            result=web.stop_sharing(self.state)
        self.assertEqual(calls,['POST','DELETE']);self.assertFalse(result['error'])

    def test_corrupt_private_state_preserves_local_mode_without_network(self):
        path=web.secret_path(self.state);path.parent.mkdir(parents=True)
        path.write_text('{}')
        with patch.object(web,'request') as call:
            self.assertTrue(web.sync_task(self.payload,self.state)['error'])
            call.assert_not_called()

    def test_parallel_clients_do_not_create_two_sessions(self):
        entered,release=threading.Event(),threading.Event()
        calls=[]
        def response(endpoint,method,path,body=None,key=None):
            identity=body.get('id') or path.rsplit('/',1)[1]
            calls.append(identity);entered.set();release.wait(3)
            return dict(id=identity,version=len(calls),expires_at=9999999999999)
        with patch.object(web,'request',side_effect=response):
            thread=threading.Thread(target=web.sync_task,args=(self.payload,self.state,'https://progress.example',True))
            thread.start();self.assertTrue(entered.wait(3))
            threading.Timer(.1,release.set).start()
            try:web.sync_task(dict(self.payload,percent=100,status='Concluído'),self.state,'https://progress.example',True)
            finally:release.set();thread.join(3)
        self.assertEqual(len(calls),2);self.assertEqual(calls[0],calls[1])

    def test_cli_keeps_local_delivery_and_publishes_only_reader_link(self):
        status=importlib.import_module('status')
        reader='https://progress.example/#'+'a'*32+'.'+'b'*43
        args=['status.py','--output',str(self.state.with_suffix('.html')),'--title','Task',
              '--percent','10','--message','Working','--web-url','https://progress.example']
        with patch.object(sys,'argv',args),patch.object(status,'sync_task',return_value={'url':reader,'error':None}):
            with contextlib.redirect_stdout(io.StringIO()):status.main()
        data=json.loads(self.state.read_text(encoding='utf-8'))
        self.assertEqual(data['web_url'],reader)
        self.assertEqual(data['percent'],10)
        self.assertIn('qr=1',self.state.with_suffix('.html').read_text(encoding='utf-8'))

    def test_cli_local_progress_survives_web_outage(self):
        status=importlib.import_module('status')
        args=['status.py','--output',str(self.state.with_suffix('.html')),'--title','Task',
              '--percent','50','--message','Working','--web-url','https://progress.example']
        with patch.object(sys,'argv',args),patch.object(status,'sync_task',return_value={'url':None,'error':'Offline'}):
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):status.main()
        self.assertEqual(json.loads(self.state.read_text(encoding='utf-8'))['percent'],50)
        self.assertTrue(self.state.with_suffix('.html').exists())

    def test_native_sharing_declined_does_not_upload(self):
        from types import SimpleNamespace
        sharing=importlib.import_module('sharing')
        app=SimpleNamespace(state=self.state,root=object(),data=self.payload)
        with patch.object(sharing,'service_url',return_value='https://progress.example'),patch.object(sharing.messagebox,'askyesno',return_value=False),patch.object(sharing,'sync_task') as upload:
            sharing.share_task(app)
            upload.assert_not_called()

    def test_revoked_cli_clears_reader_link_from_deliverables(self):
        status=importlib.import_module('status')
        self.state.write_text(json.dumps(dict(self.payload,web_url='https://progress.example/#reader')))
        self.state.with_suffix('.html').write_text('<main><p><a id="web-sharing" href="https://progress.example/#reader">Mobile</a></p></main>')
        with patch.object(sys,'argv',['status.py','--output',str(self.state.with_suffix('.html')),'--stop-sharing']),patch.object(status,'stop_sharing',return_value={'error':None}),contextlib.redirect_stdout(io.StringIO()):
            status.main()
        self.assertIsNone(json.loads(self.state.read_text()).get('web_url'))
        self.assertNotIn('web-sharing',self.state.with_suffix('.html').read_text())

    def test_creation_retry_updates_snapshot_after_lost_response(self):
        count=0
        def response(endpoint,method,path,body=None,key=None):
            nonlocal count
            count+=1
            if count==1:raise web.WebError('response lost')
            if method=='POST':return dict(id=body['id'],version=1,payload=dict(self.payload,percent=10),expires_at=9999999999999)
            self.assertEqual(method,'PATCH');self.assertEqual(body['payload']['percent'],100)
            return dict(id=path.rsplit('/',1)[1],version=2,expires_at=9999999999999)
        with patch.object(web,'request',side_effect=response):
            web.sync_task(self.payload,self.state,'https://progress.example',True)
            result=web.sync_task(dict(self.payload,percent=100,status='Concluído'),self.state,'https://progress.example',True)
        self.assertFalse(result['error']);self.assertEqual(count,3)

    def test_slow_web_response_cannot_overwrite_newer_local_completion(self):
        status=importlib.import_module('status')
        target=self.state.with_suffix('.html')
        def slow(*args):
            self.state.write_text(json.dumps(dict(self.payload,percent=100,status='Concluído',delivery_id='newer')))
            target.write_text('New completed page')
            return {'url':'https://progress.example/#reader','error':None}
        args=['status.py','--output',str(target),'--title','Task','--percent','10','--message','Working']
        with patch.object(sys,'argv',args),patch.object(status,'sync_task',side_effect=slow),contextlib.redirect_stdout(io.StringIO()):status.main()
        self.assertEqual(json.loads(self.state.read_text())['percent'],100)
        self.assertEqual(target.read_text(),'New completed page')

    def test_truncated_or_nonobject_http_response_is_sanitized(self):
        from http.client import IncompleteRead
        from unittest.mock import MagicMock
        for value in (b'null',b'[]',IncompleteRead(b'partial')):
            response=MagicMock()
            if isinstance(value,Exception):response.read.side_effect=value
            else:response.read.return_value=value
            opener=MagicMock();opener.open.return_value.__enter__.return_value=response
            with patch.object(web.urllib_request,'build_opener',return_value=opener),self.assertRaises(web.WebError):
                web.request('https://progress.example','GET','/api/health')

    def test_native_worker_exception_always_releases_sharing_action(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        sharing=importlib.import_module('sharing')
        app=SimpleNamespace(state=self.state,root=MagicMock(),data=self.payload)
        with patch.object(sharing,'service_url',return_value='https://progress.example'),patch.object(sharing.messagebox,'askyesno',return_value=True),patch.object(sharing,'sync_task',side_effect=RuntimeError('broken')),patch.object(sharing.threading,'Thread') as thread,patch.object(sharing.messagebox,'showwarning') as warning:
            thread.return_value.start.side_effect=lambda:thread.call_args.kwargs['target']()
            sharing.share_task(app)
            app.root.after.call_args.args[1]()
            self.assertFalse(app.sharing_in_flight);warning.assert_called_once()

    def test_transport_identifies_application_instead_of_default_urllib(self):
        from unittest.mock import MagicMock
        opener=MagicMock();opener.open.return_value.__enter__.return_value.read.return_value=b'{}'
        with patch.object(web.urllib_request,'build_opener',return_value=opener):web.request('https://progress.example','GET','/api/health')
        self.assertEqual(opener.open.call_args.args[0].get_header('User-agent'),'ProgressBubble/1.0')

    def test_late_client_uses_latest_saved_task_revision(self):
        self.state.write_text(json.dumps(dict(self.payload,delivery_id='new',percent=100,status='Concluído')))
        def response(endpoint,method,path,body=None,key=None):
            self.assertEqual(body['payload']['percent'],100)
            return dict(id=body['id'],version=1,expires_at=9999999999999)
        with patch.object(web,'request',side_effect=response):
            web.sync_task(dict(self.payload,delivery_id='old'),self.state,'https://progress.example',True)
