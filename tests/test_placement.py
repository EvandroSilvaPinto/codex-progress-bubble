from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))
from placement import initial_position, PositionSlot


class PlacementTests(unittest.TestCase):
    def test_parallel_bubbles_open_left_with_a_gap_at_each_scale(self):
        for dpi,bubble in ((1,.85),(1,1.2),(1.5,1.8),(2,2.4)):
            args=(3840,2160,round(360*dpi),round(360*dpi),dpi,bubble)
            first=initial_position(*args,0)
            second=initial_position(*args,1)
            self.assertGreaterEqual(first[0]-second[0],84*bubble+17*dpi)
            self.assertEqual(first[1],second[1])

    def test_rows_wrap_upward_and_stay_on_screen(self):
        positions=[initial_position(900,900,360,360,1,1,n) for n in range(6)]
        self.assertLess(positions[5][1],positions[0][1])
        self.assertEqual(len(set(positions)),len(positions))
        for x,y in positions:
            self.assertTrue(0<=x<=540)
            self.assertTrue(0<=y<=540)

    @unittest.skipUnless(sys.platform=='win32','Windows named position handles')
    def test_live_slots_are_distinct_and_released_positions_can_be_reused(self):
        first=PositionSlot()
        second=PositionSlot()
        replacement=None
        try:
            self.assertNotEqual(first.index,second.index)
            index=first.index
            first.close()
            replacement=PositionSlot()
            self.assertEqual(replacement.index,index)
        finally:
            first.close()
            second.close()
            if replacement is not None:
                replacement.close()
