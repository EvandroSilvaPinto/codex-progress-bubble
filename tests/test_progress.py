from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest
import json
import shutil
import subprocess

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))
from progress import displayed_progress, visual_state, progress_script


class EstimatedProgressTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Node is optional for checking HTML/Python parity')
    def test_html_and_native_estimates_match(self):
        for minutes in (0,3,10,60):
            now=self.start+timedelta(minutes=minutes)
            script='''const bar={}, label={};
const document={querySelector:()=>bar,getElementById:()=>label};
const setInterval=()=>{};
Date.now=()=>TIME;
'''.replace('TIME',str(round(now.timestamp()*1000)))
            script+=progress_script(self.data)+'\nconsole.log(JSON.stringify([bar.value,label.textContent]));'
            result=subprocess.run(['node'],input=script,text=True,capture_output=True,check=True)
            value,label=json.loads(result.stdout)
            self.assertAlmostEqual(value,displayed_progress(self.data,now))
            self.assertEqual(label,f'{int(value)}%')

    def setUp(self):
        self.start=datetime(2026,11,14,12,tzinfo=timezone.utc)
        self.finish=self.start+timedelta(minutes=10)
        self.data=dict(percent=10,status='Em andamento',eta_at=self.finish.isoformat())
        self.data.update(visual_state({},10,'Em andamento',self.data['eta_at'],self.start))

    def test_advances_slower_than_eta_and_stops_at_95(self):
        self.assertEqual(displayed_progress(self.data,self.start),10)
        half=displayed_progress(self.data,self.start+timedelta(minutes=5))
        self.assertAlmostEqual(half,48.25)
        self.assertAlmostEqual(displayed_progress(self.data,self.finish),86.5)
        self.assertEqual(displayed_progress(self.data,self.finish+timedelta(hours=5)),95)
        self.assertEqual(self.data['percent'],10)

    def test_revised_estimate_and_lower_report_do_not_move_visual_backwards(self):
        now=self.start+timedelta(minutes=5)
        before=displayed_progress(self.data,now)
        updated=dict(percent=20,status='Em andamento',eta_at=(now+timedelta(minutes=20)).isoformat())
        updated.update(visual_state(self.data,20,updated['status'],updated['eta_at'],now))
        self.assertEqual(displayed_progress(updated,now),before)
        self.assertGreater(displayed_progress(updated,now+timedelta(minutes=1)),before)

    def test_ordinary_updates_preserve_anchor_and_html_reload_continuity(self):
        now=self.start+timedelta(minutes=3)
        fields=visual_state(self.data,20,'Em andamento',self.data['eta_at'],now)
        updated=dict(self.data,percent=20,**fields)
        self.assertEqual(updated['visual_started_at'],self.data['visual_started_at'])
        self.assertEqual(displayed_progress(updated,now),displayed_progress(self.data,now))

    def test_wait_failure_and_stop_freeze_until_resumed_with_eta(self):
        now=self.start+timedelta(minutes=4)
        for state in ('Falha','Aguardando informação','Interrompido'):
            paused=dict(percent=10,status=state,eta_at=None)
            paused.update(visual_state(self.data,10,state,None,now))
            self.assertEqual(displayed_progress(paused,now),displayed_progress(self.data,now))
            self.assertEqual(displayed_progress(paused,now+timedelta(hours=1)),displayed_progress(paused,now))

    def test_no_eta_means_no_automatic_progress_and_only_completion_reaches_100(self):
        self.assertEqual(displayed_progress(dict(percent=30,status='Em andamento'),self.start),30)
        self.assertEqual(displayed_progress(dict(self.data,eta_at='invalid'),self.start),10)
        self.assertEqual(displayed_progress(dict(self.data,percent=98),self.finish),98)
        self.assertEqual(displayed_progress(dict(self.data,status='Concluído',percent=100),self.start),100)
