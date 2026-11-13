import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'install.py'


class InstallTests(unittest.TestCase):
    def test_global_installation_for_all_agents_in_isolated_home(self):
        with tempfile.TemporaryDirectory(prefix='agent homes ') as tmp:
            home = Path(tmp)
            env = dict(os.environ,HOME=tmp,USERPROFILE=tmp)
            cmd = [sys.executable,str(SCRIPT),'--agent','all']
            preview = subprocess.run(cmd+['--dry-run'],env=env,capture_output=True,text=True)
            self.assertEqual(preview.returncode,0,preview.stderr)
            # Check isolation before allowing the subprocess to copy files.
            self.assertEqual(preview.stdout.count(tmp),3)
            result = subprocess.run(cmd,env=env,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            for relative in ('.agents/skills','.claude/skills','.gemini/config/skills'):
                skill = home/relative/'acompanhar-demandas-longas'
                self.assertTrue((skill/'SKILL.md').is_file())
                self.assertEqual((skill/'scripts/status.py').read_bytes(),
                                 (ROOT/'skills/acompanhar-demandas-longas/scripts/status.py').read_bytes())

    def test_global_paths_follow_each_agent(self):
        self.assertTrue(SCRIPT.is_file(), 'Falta o instalador multiagente')
        spec = importlib.util.spec_from_file_location('installer', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        home = Path('/example-home')
        expected = {'codex':'.agents/skills', 'claude':'.claude/skills',
                    'antigravity':'.gemini/config/skills'}
        for agent, relative in expected.items():
            self.assertEqual(module.skill_root(agent,'user',Path('/project'),home),home/relative)

    def test_project_installation_for_all_agents_and_existing_files(self):
        self.assertTrue(SCRIPT.is_file(), 'Falta o instalador multiagente')
        with tempfile.TemporaryDirectory(prefix='three agents ') as tmp:
            project = Path(tmp)
            cmd = [sys.executable,str(SCRIPT),'--agent','all','--scope','project',
                   '--project-root',str(project)]
            dry = subprocess.run(cmd+['--dry-run'], capture_output=True)
            self.assertEqual(dry.returncode,0,dry.stderr)
            self.assertEqual(list(project.iterdir()),[])
            result = subprocess.run(cmd,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            for folder in ('.agents/skills','.claude/skills'):
                skill = project/folder/'acompanhar-demandas-longas'
                script = skill/'scripts/status.py'
                out = project/folder/'demo.html'
                run = subprocess.run([sys.executable,str(script),'--output',str(out),
                    '--title','Teste portátil','--percent','25','--message','Executando'],capture_output=True)
                self.assertEqual(run.returncode,0,run.stderr)
                self.assertTrue(out.is_file())
                sentinel = skill/'custom.txt'
                sentinel.write_text('preservar')
            repeat = subprocess.run(cmd,capture_output=True)
            self.assertNotEqual(repeat.returncode,0)
            self.assertEqual(sentinel.read_text(),'preservar')


if __name__ == '__main__':
    unittest.main()
