import unittest
from sampling import uniform,changed,hierarchical

class BudgetTests(unittest.TestCase):
    def test_budget_and_no_repeated_encodes(self):
        for n in (1,2,17,240):
            for budget in (1,2,8,16):
                seen=[]
                def encode(i):
                    self.assertTrue(0<=i<n);self.assertNotIn(i,seen);seen.append(i);return .5
                result=hierarchical(n,budget,encode)
                self.assertEqual(len(result),min(n,budget))
                self.assertEqual(set(result),set(seen))

    def test_uniform_covers_endpoints(self):
        self.assertEqual(uniform(100,2),[0,99])
        self.assertEqual(uniform(1,10),[0])

    def test_no_hint_is_not_magically_found(self):
        selected=hierarchical(240,16,lambda i:1. if 103<=i<108 else .1)
        self.assertFalse(any(103<=i<108 for i in selected))

    def test_change_chooses_clear_onset(self):
        motion=[0.]*240;motion[103]=1
        self.assertIn(103,changed(motion,16))

if __name__=='__main__':unittest.main()
