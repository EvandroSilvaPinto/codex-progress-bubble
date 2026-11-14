import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts/navigation.py'


class NavigationTests(unittest.TestCase):
    def module(self):
        self.assertTrue(SOURCE.exists(),'Falta o suporte a links de conversa')
        spec=importlib.util.spec_from_file_location('navigation',SOURCE)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_codex_current_chat_is_used_and_existing_origin_is_preserved(self):
        nav=self.module()
        thread='01a1d668-014e-7812-a458-dbc8890a3599'
        with patch.dict(os.environ,{'CODEX_THREAD_ID':thread}):
            self.assertEqual(nav.conversation_url(None,{}),'codex://threads/'+thread)
            previous={'conversation_url':'https://example.com/chat/original'}
            self.assertEqual(nav.conversation_url(None,previous),previous['conversation_url'])
            self.assertIsNone(nav.conversation_url('none',previous))

    def test_unsafe_or_non_chat_protocols_are_rejected(self):
        nav=self.module()
        for url in ('javascript:alert(1)','file:///secret','codex://threads/new',
                    'codex://settings','https://user:password@example.com','https://'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                nav.validate_url(url)

    def test_missing_origin_uses_html_instead_of_inventing_link(self):
        nav=self.module()
        with patch.dict(os.environ,{},clear=True):
            self.assertIsNone(nav.conversation_url(None,{}))
