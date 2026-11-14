import json
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'skills/progress-bubble'


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='progress bubble ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / 'installed skill'
        shutil.copytree(SOURCE, self.skill)
        self.target = self.root / 'result with spaces' / 'status.html'

    def run_status(self, percent=35, status='Em andamento', message='<script>bad()</script>', extra=()):
        return subprocess.run([sys.executable, str(self.skill/'scripts/status.py'),
            '--output',str(self.target),'--title','Relatório & revisão',
            '--percent',str(percent),'--status',status,'--message',message,*extra],
            cwd=self.root, capture_output=True, encoding='utf-8', errors='replace')

    def state(self):
        return json.loads(self.target.with_suffix('.json').read_text(encoding='utf-8'))

    def test_relocated_installation_writes_escaped_html_and_full_state(self):
        result = self.run_status()
        self.assertEqual(result.returncode, 0, result.stderr)
        page = self.target.read_text(encoding='utf-8')
        self.assertNotIn('<script>bad()</script>',page)
        self.assertIn('&lt;script&gt;bad()&lt;/script&gt;',page)
        self.assertEqual(self.state()['percent'],35)
        self.assertEqual(self.state()['title'],'Relatório & revisão')
        self.assertEqual(self.state()['html'],str(self.target.resolve()))

    def test_failure_retains_progress_and_stops_html_refresh(self):
        self.assertEqual(self.run_status(60,'Falha').returncode,0)
        self.assertEqual(self.state()['percent'],60)
        self.assertEqual(self.state()['status'],'Falha')
        self.assertNotIn('http-equiv',self.target.read_text(encoding='utf-8'))

    def test_completion_stops_html_refresh(self):
        self.assertEqual(self.run_status(100,'Concluído').returncode,0)
        self.assertEqual(self.state()['percent'],100)
        self.assertNotIn('http-equiv',self.target.read_text(encoding='utf-8'))

    def test_estimated_finish_is_saved_preserved_and_cleared_on_completion(self):
        before = datetime.now().astimezone()
        result = self.run_status(extra=('--eta-minutes','5'))
        self.assertEqual(result.returncode,0,result.stderr)
        eta = datetime.fromisoformat(self.state()['eta_at'])
        self.assertGreaterEqual((eta-before).total_seconds(),299)
        self.assertLess((eta-before).total_seconds(),310)
        self.assertIn('Faltam cerca de 5 min' if self.state().get('language')=='pt' else 'About 5 min left',self.target.read_text(encoding='utf-8'))
        self.assertEqual(self.run_status(50).returncode,0)
        self.assertEqual(self.state()['eta_at'],eta.isoformat())
        self.assertEqual(self.run_status(100,'Concluído').returncode,0)
        self.assertIsNone(self.state()['eta_at'])

    def test_invalid_estimate_preserves_previous_status(self):
        self.assertEqual(self.run_status().returncode,0)
        previous = self.state()
        for minutes in ('-1','0','nan','inf'):
            with self.subTest(minutes=minutes):
                self.assertNotEqual(self.run_status(extra=('--eta-minutes',minutes)).returncode,0)
                self.assertEqual(self.state(),previous)

    def test_dismiss_only_the_selected_completed_demand(self):
        command = [sys.executable,str(self.skill/'scripts/status.py'),
                   '--output',str(self.target),'--dismiss-completed']
        self.assertEqual(self.run_status(35).returncode,0)
        before = self.state()
        self.assertEqual(subprocess.run(command,capture_output=True).returncode,0)
        self.assertEqual(self.state(),before)
        self.assertEqual(self.run_status(100,'Concluído').returncode,0)
        html_before = self.target.read_bytes()
        self.assertEqual(subprocess.run(command,capture_output=True).returncode,0)
        self.assertTrue(self.state()['dismissed'])
        self.assertEqual(self.target.read_bytes(),html_before)
        self.assertEqual(self.run_status(10).returncode,0)
        self.assertNotIn('dismissed',self.state())

    def test_invalid_update_preserves_previous_state(self):
        self.assertEqual(self.run_status().returncode,0)
        previous = self.state()
        for percent,status in [(-1,'Em andamento'),(101,'Em andamento'),
                               (100,'Em andamento'),(70,'Concluído')]:
            with self.subTest(percent=percent,status=status):
                self.assertNotEqual(self.run_status(percent,status).returncode,0)
                self.assertEqual(self.state(),previous)

    def test_active_update_replaces_same_files(self):
        self.assertEqual(self.run_status(10).returncode,0)
        self.assertEqual(self.run_status(70,message='Revisando').returncode,0)
        self.assertEqual(self.state()['percent'],70)
        self.assertEqual(self.state()['message'],'Revisando')
        self.assertIn('http-equiv',self.target.read_text(encoding='utf-8'))
        self.assertEqual(len(list(self.target.parent.iterdir())),2)


if __name__ == '__main__':
    unittest.main()
