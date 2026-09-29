import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from worker import bv1_paths,LUNA_ARM
class Arm(unittest.TestCase):
 def test_legacy_unchanged(self):
  a,b,c=bv1_paths({'analysis_root':'/repo'},Path('/phase'))
  self.assertEqual(str(b),'/repo/analysis/freeflow/personality-eval-bv1/outputs')
  self.assertEqual(c,Path('/phase/bv1_bindings'))
 def test_isolated(self):
  a,b,c=bv1_paths({'analysis_root':'/repo','bv1_evaluator':LUNA_ARM},Path('/phase'))
  self.assertIn('/arms/'+LUNA_ARM+'/',str(b));self.assertNotEqual(c,Path('/phase/bv1_bindings'))
 def test_unknown_rejected(self):
  with self.assertRaises(AssertionError):bv1_paths({'analysis_root':'/repo','bv1_evaluator':'unknown'},Path('/phase'))
