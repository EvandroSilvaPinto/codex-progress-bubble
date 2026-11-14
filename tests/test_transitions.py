import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))

class Root:
    def __init__(self):self.jobs={};self.number=0
    def after(self,ms,fn):self.number+=1;self.jobs[self.number]=fn;return self.number
    def after_cancel(self,job):self.jobs.pop(job,None)
    def tick(self):
        jobs=list(self.jobs.values());self.jobs.clear()
        for fn in jobs:fn()
class Canvas:
    def __init__(self):self.positions={1:[0,0],2:[0,0],3:[0,0]}
    def find_withtag(self,tag):return (1,2)
    def move(self,item,x,y):self.positions[item][0]+=x;self.positions[item][1]+=y

class TransitionTests(unittest.TestCase):
    def motion(self,enabled=True):
        from transitions import PanelMotion
        self.root=Root();self.canvas=Canvas();self.time=[0]
        return PanelMotion(self.root,self.canvas,enabled=enabled,clock=lambda:self.time[0])
    def test_enter_moves_card_only_and_finishes_at_exact_original_position(self):
        motion=self.motion();calls=[]
        motion.enter(lambda:calls.append('draw'))
        self.assertEqual(calls,['draw']);self.assertGreater(self.canvas.positions[1][0],0)
        self.assertEqual(self.canvas.positions[3],[0,0])
        self.time[0]=1;self.root.tick()
        self.assertEqual(self.canvas.positions[1],[0,0]);self.assertFalse(self.root.jobs)
    def test_exit_draws_collapsed_view_only_after_animation(self):
        motion=self.motion();calls=[];motion.exit(lambda:calls.append('closed'))
        self.assertEqual(calls,[])
        self.time[0]=1;self.root.tick();self.assertEqual(calls,['closed'])
    def test_repeated_changes_cancel_old_frames_without_coordinate_drift(self):
        motion=self.motion();motion.enter(lambda:None);motion.enter(lambda:None)
        self.time[0]=1;self.root.tick()
        self.assertEqual(self.canvas.positions[1],[0,0]);self.assertFalse(self.root.jobs)
    def test_reduced_motion_renders_immediately_without_timers(self):
        motion=self.motion(False);calls=[]
        motion.enter(lambda:calls.append('open'));motion.exit(lambda:calls.append('closed'))
        self.assertEqual(calls,['open','closed']);self.assertFalse(self.root.jobs)
