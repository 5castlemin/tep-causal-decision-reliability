"""Software fixtures only; no external import, pickle load, or simulator test."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from src.causalman_micro_acceptance import PIN, GIB, admit, verdict, verify_files, two_step_hedge, hard_do_parent_edges, git_tree_hash, verify_manifest_tree

class AcceptanceSafeguardsTest(unittest.TestCase):
    def test_git_tree_authentication_primitive(self):
        self.assertEqual(git_tree_hash([]),'4b825dc642cb6eb9a060e54bf8d69288fbee4904')
        blob=hashlib.sha1(b'blob 1\0x').hexdigest()
        record={'name':'x','mode':'100644','type':'blob','sha':blob}
        expected=hashlib.sha1(b'tree 29\0'+b'100644 x\0'+bytes.fromhex(blob)).hexdigest()
        self.assertEqual(git_tree_hash([record]),expected)
        with self.assertRaisesRegex(ValueError,'WRONG_TREE'):
            verify_manifest_tree({'tree':'0'*40},{'sha':'0'*40,'tree':[]})

    def test_constant_term_does_not_certify_mutilated_graph(self):
        graph={"nodes":{"A":{"term":"16000"}},"edges":[["U","A","",{}],["A","Y","",{}]]}
        self.assertEqual(len(hard_do_parent_edges(graph,'A')),1)
        graph['edges']=graph['edges'][1:]
        self.assertEqual(hard_do_parent_edges(graph,'A'),[])

    def test_typed_hedge_certificate_not_bidirected_as_dag(self):
        e=[('A','M','directed'),('M','Y','directed'),
           ('A','M','bidirected'),('M','Y','bidirected')]
        self.assertTrue(two_step_hedge(e,'A','M','Y'))
        self.assertFalse(two_step_hedge(e[:-1],'A','M','Y'))
        self.assertFalse(two_step_hedge([(u,v,'directed') for u,v,_ in e],'A','M','Y'))
        self.assertFalse(two_step_hedge(e,'A','A','Y'))

    def test_admission_limits(self):
        self.assertEqual(admit(100,100,3*GIB,3*GIB,1),[])
        self.assertIn("DOWNLOAD_LIMIT",admit(GIB+1,1,3*GIB,3*GIB,1))
        self.assertIn("DISK_LIMIT",admit(1,2*GIB+1,3*GIB,3*GIB,1))
        self.assertIn("AVAILABLE_MEMORY",admit(1,1,3*GIB,GIB,1))
        self.assertIn("WALL_LIMIT",admit(1,1,3*GIB,3*GIB,1800))

    def test_infrastructure_not_scientific_rejection(self):
        self.assertEqual(verdict({"resources":"RESOURCE_BLOCKED"}),"CONDITIONAL_NOT_ACCEPTED")
        self.assertEqual(verdict({"rights":"UNKNOWN"}),"CONDITIONAL_NOT_ACCEPTED")
        self.assertEqual(verdict({"active_reference":"FAIL"}),"REJECTED_FOR_ORIGINAL_HYPOTHESIS")

    def test_partial_not_accepted(self):
        self.assertEqual(verdict({"api":"PASS","hard_do":"PASS"}),"CONDITIONAL_NOT_ACCEPTED")

    def test_all_gates_required(self):
        keys=("resources","rights","api","active_reference","observed_reference","hard_do",
              "outcome","seed_replay","identification_support","decision_contract")
        self.assertEqual(verdict(dict.fromkeys(keys,"PASS")),"ACCEPTED_FOR_PILOT_DESIGN")
        for k in keys:
            g=dict.fromkeys(keys,"PASS");g[k]="NOT_RUN"
            self.assertNotEqual(verdict(g),"ACCEPTED_FOR_PILOT_DESIGN")

    def test_artifact_verification_and_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"fixture.txt";b=b"software fixture";p.write_bytes(b)
            record={"path":p.name,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),
                    "git_blob_sha1":hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()}
            manifest={"commit":PIN,"files":[record]}
            self.assertEqual(verify_files(td,manifest),1)
            p.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError,"HASH_MISMATCH"):
                verify_files(td,manifest)
            manifest["commit"]="0"*40
            with self.assertRaisesRegex(ValueError,"COMMIT"):
                verify_files(td,manifest)
            manifest["commit"]=PIN;p.write_bytes(b)
            (Path(td)/'unverified.py').write_text('not executed')
            with self.assertRaisesRegex(ValueError,'UNVERIFIED_EXTRA'):
                verify_files(td,manifest)

    def test_escape_refused(self):
        with self.assertRaisesRegex(ValueError,"ESCAPING"):
            verify_files(".",{"commit":PIN,"files":[{"path":"../not-a-model"}]})

if __name__ == "__main__":
    unittest.main()
