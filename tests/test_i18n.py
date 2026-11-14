import contextlib
from datetime import datetime, timedelta
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))
import i18n
import status
from timing import eta_text


class LanguageTests(unittest.TestCase):
    def tearDown(self):
        i18n.system_language.cache_clear()

    def test_portuguese_variants_and_other_language_fallback(self):
        for name in ('pt','pt-BR','pt_PT','pt_BR.UTF-8'):
            self.assertEqual(i18n.language_for(name),'pt')
        for name in ('en-US','de_DE','C',None):
            self.assertEqual(i18n.language_for(name),'en')

    def test_windows_uses_display_language_not_regional_number_format(self):
        kernel=SimpleNamespace(GetUserDefaultUILanguage=Mock(return_value=0x0416))
        with patch.object(i18n,'os',SimpleNamespace(name='nt',environ={'LANG':'en_US'})), \
             patch.object(i18n.ctypes,'WinDLL',return_value=kernel,create=True):
            i18n.system_language.cache_clear()
            self.assertEqual(i18n.system_language(),'pt')

    def test_non_windows_locale_priority(self):
        with patch.object(i18n,'os',SimpleNamespace(name='posix',environ={
                'LC_MESSAGES':'en_GB.UTF-8','LANG':'pt_BR.UTF-8'})):
            i18n.system_language.cache_clear()
            self.assertEqual(i18n.system_language(),'en')

    def test_eta_is_localized_without_changing_canonical_status(self):
        now=datetime.now().astimezone()
        data=dict(status='Em andamento',eta_at=(now+timedelta(minutes=3)).isoformat())
        self.assertEqual(eta_text(data,now,language='en'),'About 3 min left')
        self.assertEqual(eta_text(data,now,language='pt'),'Faltam cerca de 3 min')
        self.assertEqual(data['status'],'Em andamento')

    def test_html_labels_javascript_and_accessibility_follow_language(self):
        for language,label,html_lang in (('pt','Em andamento','pt-BR'),('en','In progress','en')):
            with tempfile.TemporaryDirectory() as tmp:
                target=Path(tmp)/'demo.html'
                args=['status.py','--output',str(target),'--title','Cores',
                      '--percent','40','--message','Texto do usuário','--eta-minutes','3']
                with patch.object(sys,'argv',args),patch.object(status,'system_language',return_value=language), \
                     contextlib.redirect_stdout(io.StringIO()):
                    status.main()
                page=target.read_text(encoding='utf-8')
                data=json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))
                self.assertIn(f'lang="{html_lang}"',page)
                self.assertIn(label,page)
                self.assertIn('<h1>Cores</h1>',page)
                self.assertIn('Texto do usuário',page)
                self.assertIn('Estimated progress' if language=='en' else 'Progresso estimado',page)
                self.assertIn('Recalculating estimate' if language=='en' else 'Recalculando previsão',page)
                self.assertEqual(data['status'],'Em andamento')
                self.assertEqual(data['language'],language)
