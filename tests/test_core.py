import unittest,copy,json
from wheel_record_integrity import run
DEMO={'files': {'example/__init__.py': 'answer=42\n'}, 'tamper': 'example/__init__.py'}
class DomainTests(unittest.TestCase):
 def test_bytes_tampering_detected(self):
  x=run(DEMO);self.assertFalse(x['valid']);self.assertEqual({f['code']for f in x['findings']},{'hash_mismatch','size_mismatch'})
 def test_correct_record(self):
  x=run({'files':DEMO['files']});self.assertTrue(x['valid']);self.assertFalse(x['publisher_identity_authenticated'])
 def test_invalid_archive(self):
  with self.assertRaises(ValueError):run({'wheel_base64':'YWJj'})
