"""Window control behavior without requiring a graphical desktop."""
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))
from bubble import Bubble
from sizing import geometry, DEFAULTS
from colors import DEFAULTS as COLORS


class BubbleControlTests(unittest.TestCase):
    def test_english_card_renders_labels_but_preserves_user_title_and_message(self):
        app=self.bubble()
        app.theme=dict(COLORS)
        app.tooltip=Mock()
        app.data=dict(title='Cores',message='Texto',status='Em andamento',percent=65)
        with patch('i18n.system_language',return_value='en'),patch('bubble.tk.PhotoImage'):
            Bubble.draw(app)
        labels=[call.kwargs.get('text') for call in app.canvas.create_text.call_args_list]
        self.assertIn('PROGRESS',labels)
        self.assertIn('Colors',labels)
        self.assertIn('Cores',labels)
        self.assertIn('Texto',labels)
        self.assertIn('▶ In progress',labels)

    def bubble(self, scale=1):
        app = Bubble.__new__(Bubble)
        app.expanded = True
        app.colors_open = False
        app.bubble_hover = False
        app.close_hide_job = None
        app.down = (0, 0, 0, 0)
        app.scale = scale
        app.layout = geometry(scale,DEFAULTS)
        app.canvas = Mock()
        app.root = Mock()
        app.draw = Mock()
        app.draw_bubble_close = Mock()
        return app

    def test_card_close_preserves_window_and_allows_reopening(self):
        app = self.bubble()
        app.close_card()
        self.assertFalse(app.expanded)
        self.assertIsNone(app.down)
        app.root.destroy.assert_not_called()
        app.press(SimpleNamespace(x_root=0, y_root=0))
        app.release(None)
        self.assertTrue(app.expanded)

    def test_card_close_also_retracts_color_panel(self):
        app = self.bubble()
        app.colors_open = True
        app.set_color_panel = Mock()
        app.close_card()
        self.assertFalse(app.expanded)
        app.set_color_panel.assert_called_once_with(False)
        app.root.destroy.assert_not_called()

    def test_close_stays_visible_when_pointer_moves_from_ring_to_button(self):
        for scale, palette in ((1, False), (1.5, True), (2, False)):
            app = self.bubble(scale)
            app.colors_open = palette
            app.layout = geometry(scale,DEFAULTS,palette)
            bx,by = app.layout['bubble_x'],app.layout['bubble_y']
            for x, y in ((42, 42), (69, -8)):
                app.hover_bubble(SimpleNamespace(x=bx+x*scale, y=by+y*scale))
                self.assertTrue(app.bubble_hover)
            app.hover_bubble(SimpleNamespace(x=40*scale, y=40*scale))
            self.assertFalse(app.bubble_hover)
            app.hide_bubble_close()
            app.canvas.delete.assert_called_with('bubble-close')


if __name__ == '__main__':
    unittest.main()
