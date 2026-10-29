"""Tests use a tiny mock archive, not scientific simulator data."""
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/'research_runs'/'tep_matlab_local_validation'/'prepare_official_source.py'
spec=importlib.util.spec_from_file_location('matlab_stage',SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class MatlabStageTests(unittest.TestCase):
    def test_verify_stage_and_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); archive=root/'source.zip'; dest=root/'new'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('temexd_mod/temexd_mod.c',b'test source')
                z.writestr('temexd_mod/TEplot.m',b'test plot')
            sha=lambda b: hashlib.sha256(b).hexdigest()
            manifest={'archive_sha256':sha(archive.read_bytes()),'files':{'temexd_mod.c':sha(b'test source')}}
            (root/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest),encoding='utf8')
            with patch.object(module,'ROOT',root), patch.object(sys,'argv',['prepare','--archive',str(archive),'--destination',str(dest)]), contextlib.redirect_stdout(io.StringIO()):
                module.main()
                self.assertEqual((dest/'temexd_mod.c').read_bytes(),b'test source')
                with self.assertRaises(FileExistsError):module.main()
                archive.write_bytes(b'modified')
                with self.assertRaises(ValueError):module.main()

if __name__=='__main__':unittest.main()
