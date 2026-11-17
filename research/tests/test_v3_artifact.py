"""Regression for numpy integer vocabulary serialization, no ML imports."""
import json
import unittest
from research.muhu_v3.artifact import normalize_vocabulary

class FakeNpInt:
    def __init__(self,n):self.n=n
    def __index__(self):return self.n

class ArtifactContractTests(unittest.TestCase):
    def test_numpy_like_scalar_is_normalized(self):
        result=normalize_vocabulary({"source":FakeNpInt(1),"sample":FakeNpInt(0)})
        self.assertEqual(result,{"source":1,"sample":0})
        self.assertEqual(json.loads(json.dumps(result)),result)

    def test_float_bool_and_duplicate_indices_refused(self):
        for item in (
            {"source":1.2},
            {"source":True},
            {"source":0,"sample":0},
            {"source":0,"sample":2},
            {}
        ):
            with self.assertRaises((ValueError,TypeError)):
                normalize_vocabulary(item)

if __name__=="__main__":unittest.main()
