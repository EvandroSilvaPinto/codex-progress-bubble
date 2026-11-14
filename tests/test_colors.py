import importlib.util
from pathlib import Path
import tempfile
import unittest

SOURCE=Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts/colors.py'


class ColorTests(unittest.TestCase):
    def module(self):
        self.assertTrue(SOURCE.exists(),'Falta configuração editável de cores')
        spec=importlib.util.spec_from_file_location('colors',SOURCE)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_individual_color_is_persisted_and_other_defaults_remain(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'colors.json'
            theme=module.load_colors(path)
            theme['ring']='#F3A9CE'
            module.save_colors(theme,path)
            loaded=module.load_colors(path)
            self.assertEqual(loaded['ring'],'#f3a9ce')
            self.assertEqual(loaded['background'],module.DEFAULTS['background'])

    def test_invalid_colors_do_not_replace_saved_preferences(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'colors.json'
            module.save_colors(module.DEFAULTS,path)
            before=path.read_bytes()
            for value in ('red','#123','not-a-color'):
                with self.subTest(value=value),self.assertRaises(ValueError):
                    module.save_colors(dict(module.DEFAULTS,ring=value),path)
                self.assertEqual(path.read_bytes(),before)

    def test_missing_or_corrupt_preferences_use_defaults(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'colors.json'
            self.assertEqual(module.load_colors(path),module.DEFAULTS)
            path.write_text('{broken')
            self.assertEqual(module.load_colors(path),module.DEFAULTS)

    def test_five_main_colors_update_their_related_elements(self):
        module=self.module()
        self.assertEqual(len(module.MAIN_COLORS),5)
        original=dict(module.DEFAULTS)
        theme=module.set_main_color(original,'ring','#f3a9ce')
        for key in ('ring','bar','ongoing'):
            self.assertEqual(theme[key],'#f3a9ce')
        self.assertEqual(theme['links'],original['links'])
        self.assertEqual(original,module.DEFAULTS)
        theme=module.set_main_color(theme,'background','#ffffff')
        self.assertEqual(theme['bubble_background'],'#ffffff')
        self.assertNotEqual(theme['track'],original['track'])
        theme=module.set_main_color(theme,'complete','#123456')
        self.assertEqual({theme[k] for k in ('complete','error','waiting')},{'#123456'})
