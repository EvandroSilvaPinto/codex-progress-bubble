import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bubble_installer', ROOT/'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class UpdateTests(unittest.TestCase):
    def prepare(self, tmp):
        root = Path(tmp)
        source, target = root/'source', root/'agent/skills/progress-bubble'
        for folder in (source, target):
            folder.mkdir(parents=True)
            (folder/'SKILL.md').write_text('---\nname: progress-bubble\n---\n', encoding='utf-8')
        (source/'version.txt').write_text('new')
        (target/'version.txt').write_text('old')
        (target/'custom.txt').write_text('local customization')
        return source, target

    def test_update_keeps_complete_previous_version_outside_discovery_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = self.prepare(tmp)
            backup = installer.install_skill(source, target, update=True)
            self.assertEqual((target/'version.txt').read_text(), 'new')
            self.assertEqual((backup/'version.txt').read_text(), 'old')
            self.assertEqual((backup/'custom.txt').read_text(), 'local customization')
            self.assertEqual(backup.parent, target.parent.parent/'progress-bubble-backups')

    def test_failed_replacement_restores_installed_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = self.prepare(tmp)
            original = Path.rename

            def failing_rename(path, destination):
                if path.parent.name.startswith('staging-'):
                    raise OSError('Replacement unavailable')
                return original(path, destination)

            with patch.object(Path, 'rename', failing_rename):
                with self.assertRaises(OSError):
                    installer.install_skill(source, target, update=True)
            self.assertEqual((target/'version.txt').read_text(), 'old')
            self.assertTrue((target/'custom.txt').exists())

    def test_update_refuses_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = self.prepare(tmp)
            (target/'SKILL.md').write_text('name: unrelated')
            with self.assertRaises(ValueError):
                installer.install_skill(source, target, update=True)
            self.assertEqual((target/'version.txt').read_text(), 'old')
