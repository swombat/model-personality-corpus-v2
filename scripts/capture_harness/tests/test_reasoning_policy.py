import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from worker import raw_problem,prompts
class ReasoningPolicyTest(unittest.TestCase):
 def test_explicit_policy_requires_matching_capture_receipt(self):
  c={'model':'test/model','or_provider':'Test','reasoning_effort':'medium'}
  d={'condition':'CTRL1','prompt':prompts('values')['CTRL1'],'result':'answer','raw':{'model':'test/model','provider':'Test','choices':[{'finish_reason':'stop','message':{'content':'answer'}}]}}
  self.assertEqual(raw_problem(d,c,'values','CTRL1_1'),'reasoning_policy')
  d['capture_policy']={'reasoning_effort':'high'}
  self.assertEqual(raw_problem(d,c,'values','CTRL1_1'),'reasoning_policy')
  d['capture_policy']['reasoning_effort']='medium'
  self.assertIsNone(raw_problem(d,c,'values','CTRL1_1'))
  del c['reasoning_effort'];del d['capture_policy']
  self.assertIsNone(raw_problem(d,c,'values','CTRL1_1'))
