import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'skills/acompanhar-demandas-longas'


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='progress bubble ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / 'installed skill'
        shutil.copytree(SOURCE, self.skill)
        self.target = self.root / 'result with spaces' / 'status.html'

    def run_status(self, percent=35, status='Em andamento', message='<script>bad()</script>'):
        return subprocess.run([sys.executable, str(self.skill/'scripts/status.py'),
            '--output',str(self.target),'--title','Relatório & revisão',
            '--percent',str(percent),'--status',status,'--message',message],
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
