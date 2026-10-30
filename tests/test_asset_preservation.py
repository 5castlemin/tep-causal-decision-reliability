import unittest,sys,subprocess,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from asset_preservation import append_only_preserved,assert_protected_preserved
class PreservationTests(unittest.TestCase):
 def test_append_only_and_newlines(self):
  self.assertTrue(append_only_preserved(b'old\n',b'old\r\nnew\r\n'))
  self.assertFalse(append_only_preserved(b'old\n',b'changed\nnew\n'))
  self.assertFalse(append_only_preserved(b'old\n',b''))
 def test_raw_asset_is_never_exempted(self):
  with tempfile.TemporaryDirectory() as t:
   def git(*args):return subprocess.check_output(['git',*args],cwd=t,stderr=subprocess.STDOUT)
   git('init');git('config','user.email','test@example.invalid');git('config','user.name','test')
   p=Path(t)/'data';p.mkdir();f=p/'raw.csv';f.write_bytes(b'original');git('add','.');git('commit','-m','base');base=git('rev-parse','HEAD').decode().strip();f.write_bytes(b'modified')
   with self.assertRaises(AssertionError):assert_protected_preserved(t,base,['data'])
if __name__=='__main__':unittest.main()
