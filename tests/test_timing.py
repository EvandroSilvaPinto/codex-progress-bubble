from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import unittest
import sys

SOURCE = Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts/timing.py'
sys.path.insert(0,str(SOURCE.parent))
spec = importlib.util.spec_from_file_location('timing',SOURCE)
timing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timing)


class TimingTests(unittest.TestCase):
    def test_estimate_shows_only_rounded_remaining_minutes(self):
        now = datetime(2026,11,13,20,40,tzinfo=timezone(timedelta(hours=-4)))
        data = dict(status='Em andamento',eta_at=(now+timedelta(minutes=3,seconds=10)).isoformat())
        self.assertEqual(timing.eta_text(data,now,language="pt"),'Faltam cerca de 4 min')

    def test_short_estimate_avoids_false_precision(self):
        now = datetime.now().astimezone()
        data = dict(status='Em andamento',eta_at=(now+timedelta(seconds=25)).isoformat())
        self.assertEqual(timing.eta_text(data,now,language="pt"),'Menos de 1 min')

    def test_overdue_deadline_is_not_silently_extended(self):
        now = datetime.now().astimezone()
        data = dict(status='Em andamento',eta_at=(now-timedelta(seconds=1)).isoformat())
        self.assertEqual(timing.eta_text(data,now,language="pt"),'Recalculando previsão')

    def test_waiting_and_completed_do_not_show_remaining_time(self):
        for status,label in [('Aguardando informação','Previsão suspensa'),
                             ('Concluído','Finalizado')]:
            self.assertEqual(timing.eta_text(dict(status=status,eta_at=datetime.now().astimezone().isoformat()),language="pt"),label)
