"""Keep scientific assets immutable; allow only appended historical status notes."""
from pathlib import Path
import subprocess

APPEND_ONLY = {'experiments/pilot/TASK_SPEC.md','experiments/pilot/PILOT_RESULT.md'}

def append_only_preserved(before, after):
    # Git and Windows checkouts may differ only in newline encoding.
    return after.replace(b'\r\n',b'\n').startswith(before.replace(b'\r\n',b'\n'))

def assert_protected_preserved(root, base, protected):
    root=Path(root)
    changed=subprocess.check_output(['git','diff',base,'--name-only','--',*protected],cwd=root,text=True).splitlines()
    for path in changed:
        assert path in APPEND_ONLY, 'protected asset changed: '+path
        before=subprocess.check_output(['git','show',base+':'+path],cwd=root)
        target=root/path
        assert target.is_file() and append_only_preserved(before,target.read_bytes()), 'historical content changed: '+path
    return changed
