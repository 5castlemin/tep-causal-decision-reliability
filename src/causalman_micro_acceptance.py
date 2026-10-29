"""Acceptance safeguards only. Does not import CausalMan, fit models, or score F1."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

PIN = "17529dad5ec8b8c691494c617b9af4533aa44bf8"
TREE = "07d305edf35d07b3caa9b1ebabeb3f244cdc5dc9"
GIB = 1024 ** 3

def git_tree_hash(entries):
    ordered=sorted(entries,key=lambda e:(e["name"]+("/" if e["type"]=="tree" else "")).encode())
    body=b"".join((e["mode"].lstrip("0")+" "+e["name"]).encode()+b"\0"+bytes.fromhex(e["sha"]) for e in ordered)
    return hashlib.sha1(b"tree "+str(len(body)).encode()+b"\0"+body).hexdigest()

def verify_manifest_tree(manifest, tree):
    """Authenticate selected leaf hashes against the pinned complete Git tree."""
    if tree.get("truncated") or tree["sha"]!=TREE or manifest["tree"]!=TREE:
        raise ValueError("INCOMPLETE_OR_WRONG_TREE")
    groups={"":[]};lookup={}
    for e in tree["tree"]:
        path=Path(e["path"]).as_posix();lookup[path]=e
        parent,_,name=path.rpartition("/")
        groups.setdefault(parent,[]).append(dict(e,name=name))
        if e["type"]=="tree":groups.setdefault(path,[])
    computed={}
    for path in sorted(groups,key=lambda p:p.count("/")+bool(p),reverse=True):
        for e in groups[path]:
            if e["type"]=="tree":
                child=(path+"/" if path else "")+e["name"]
                if computed[child]!=e["sha"]:raise ValueError("GIT_TREE_HASH_MISMATCH")
        computed[path]=git_tree_hash(groups[path])
    if computed[""]!=TREE:raise ValueError("GIT_ROOT_HASH_MISMATCH")
    expected={p for p,e in lookup.items() if e["type"]=="blob" and (
        p.startswith("causalman/dataset_objects/causalman_micro/") or
        (p.startswith("causalman/") and p.endswith(".py") and "/dataset_objects/" not in p) or
        p in {"LICENSE","3rd-party-licenses.txt","README.md","pyproject.toml","requirements.txt","causalman/dataset_objects/__init__.py"})}
    if {r["path"] for r in manifest["files"]}!=expected:
        raise ValueError("INCOMPLETE_SELECTED_MANIFEST")
    for r in manifest["files"]:
        if lookup.get(r["path"],{}).get("sha")!=r["git_blob_sha1"]:
            raise ValueError("MANIFEST_NOT_IN_PINNED_TREE")
    return computed[""]

def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify_files(root, manifest):
    if manifest["commit"] != PIN:
        raise ValueError("SOURCE_COMMIT_MISMATCH")
    checked = 0
    base = Path(root).resolve()
    expected={r["path"] for r in manifest["files"]}
    for item in manifest["files"]:
        p = (base / item["path"]).resolve()
        if not p.is_relative_to(base) or not p.is_file():
            raise ValueError("MISSING_OR_ESCAPING_ARTIFACT")
        b = p.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()
        if len(b) != item["bytes"] or hashlib.sha256(b).hexdigest() != item["sha256"] or blob != item["git_blob_sha1"]:
            raise ValueError("ARTIFACT_HASH_MISMATCH")
        checked += 1
    for path in base.rglob("*"):
        if path.is_file() and path.relative_to(base).as_posix() not in expected:
            if not ("__pycache__" in path.parts and path.suffix==".pyc"):
                raise ValueError("UNVERIFIED_EXTRA_FILE")
    return checked

def directory_bytes(root):
    return sum(p.stat().st_size for p in Path(root).rglob("*") if p.is_file())

def available_memory_bytes():
    if os.name != "nt":
        raise RuntimeError("Windows resource measurement required")
    class Status(ctypes.Structure):
        _fields_=[("length",ctypes.c_ulong),("load",ctypes.c_ulong)]+[
            (n,ctypes.c_ulonglong) for n in ("total","available","totalpage","availablepage","totalvirtual","availablevirtual","extended")]
    s=Status();s.length=ctypes.sizeof(s)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s)):
        raise ctypes.WinError()
    return int(s.available)

def hard_do_parent_edges(snapshot, action):
    """Snapshot edge entries are (source,target,key,attributes); preserve types."""
    return [edge for edge in snapshot["edges"] if edge[1]==action]

def admit(download_bytes, disk_bytes, free_disk, free_memory, elapsed):
    reasons = []
    if download_bytes > GIB:
        reasons.append("DOWNLOAD_LIMIT")
    if disk_bytes > 2*GIB or free_disk < 2*GIB:
        reasons.append("DISK_LIMIT")
    if free_memory < 2*GIB:
        reasons.append("AVAILABLE_MEMORY")
    if elapsed >= 1800:
        reasons.append("WALL_LIMIT")
    return reasons

def verdict(gates):
    """Infrastructure limitations are never scientific rejection."""
    if any(gates.get(k) == "FAIL" for k in ("active_reference", "observed_reference", "hard_do", "decision_contract")):
        return "REJECTED_FOR_ORIGINAL_HYPOTHESIS"
    required = ("resources", "rights", "api", "active_reference", "observed_reference",
                "hard_do", "outcome", "seed_replay", "identification_support", "decision_contract")
    if all(gates.get(k) == "PASS" for k in required):
        return "ACCEPTED_FOR_PILOT_DESIGN"
    return "CONDITIONAL_NOT_ACCEPTED"

def two_step_hedge(edges, action, mediator, outcome):
    """Check a sufficient hedge certificate, not a general ID implementation.

    F: A->M->Y, A<->M<->Y; F': M->Y, M<->Y. Both selected
    subgraphs are Y-rooted C-forests; F contains A and F' does not.
    Y remains its own ancestor after cutting A. Thus the generic nonparametric
    ADMG query is not graph-identified (Shpitser/Pearl 2006, Theorem4).
    This is conditional on the supplied graph being a valid reference; it does
    not disprove identification using additional known physical functions.
    """
    directed={(u,v) for u,v,kind in edges if kind=="directed"}
    bidirected={frozenset((u,v)) for u,v,kind in edges if kind=="bidirected"}
    return (len({action,mediator,outcome})==3 and
            {(action,mediator),(mediator,outcome)} <= directed and
            {frozenset((action,mediator)),frozenset((mediator,outcome))} <= bidirected)

def bounded_process(command, cwd, scratch, log, seconds):
    """Windows job memory cap + monitored RSS/wall/disk; fail closed if job setup fails.

    A worker must wait for START on stdin before importing/loading external code.
    A job/venv is not a security proof for arbitrary pickles. Only verified official
    objects are eligible and the worker additionally denies networking/subprocesses.
    """
    if os.name != "nt":
        raise RuntimeError("Windows job containment required by this execution contract")
    from ctypes import wintypes as w
    class Basic(ctypes.Structure):
        _fields_ = [("user",ctypes.c_longlong),("job",ctypes.c_longlong),("flags",w.DWORD),
                    ("minws",ctypes.c_size_t),("maxws",ctypes.c_size_t),("active",w.DWORD),
                    ("affinity",ctypes.c_size_t),("priority",w.DWORD),("scheduling",w.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(x,ctypes.c_ulonglong) for x in ("read","write","other","readbytes","writebytes","otherbytes")]
    class Limits(ctypes.Structure):
        _fields_ = [("basic",Basic),("io",IO),("processmem",ctypes.c_size_t),("jobmem",ctypes.c_size_t),
                    ("peakprocess",ctypes.c_size_t),("peakjob",ctypes.c_size_t)]
    class Memory(ctypes.Structure):
        _fields_ = [("cb",w.DWORD),("faults",w.DWORD)]+[(x,ctypes.c_size_t) for x in
                    ("peakws","ws","peakpaged","paged","peaknonpaged","nonpaged","pagefile","peakpagefile")]
    k = ctypes.WinDLL("kernel32",use_last_error=True)
    k.CreateJobObjectW.restype = w.HANDLE
    k.SetInformationJobObject.argtypes = [w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD]
    k.AssignProcessToJobObject.argtypes = [w.HANDLE,w.HANDLE]
    k.CloseHandle.argtypes = [w.HANDLE]
    getmem = ctypes.WinDLL("psapi").GetProcessMemoryInfo
    getmem.argtypes = [w.HANDLE,ctypes.c_void_p,w.DWORD]
    k.QueryInformationJobObject.argtypes = [w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD,ctypes.c_void_p]
    k.OpenProcess.argtypes = [w.DWORD,w.BOOL,w.DWORD]
    k.OpenProcess.restype = w.HANDLE
    class Pids(ctypes.Structure):
        _fields_ = [("assigned",w.DWORD),("count",w.DWORD),("pids",ctypes.c_size_t*64)]
    def job_peak_rss(job):
        ids=Pids()
        if not k.QueryInformationJobObject(job,3,ctypes.byref(ids),ctypes.sizeof(ids),None):
            raise ctypes.WinError(ctypes.get_last_error())
        total=0
        for pid in ids.pids[:ids.count]:
            handle=k.OpenProcess(0x410,False,int(pid))
            if handle:
                try:
                    mem=Memory();mem.cb=ctypes.sizeof(mem)
                    if getmem(handle,ctypes.byref(mem),mem.cb):
                        total+=int(mem.peakws)
                finally:
                    k.CloseHandle(handle)
        return total
    job = k.CreateJobObjectW(None,None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    lim = Limits()
    lim.basic.flags = 0x2000 | 0x200 | 0x8
    # venv launchers delegate to a base interpreter; sampling audit denies
    # application subprocesses. All setup/interpreter children share the cap.
    lim.basic.active = 8
    lim.jobmem = 2*GIB
    if not k.SetInformationJobObject(job,9,ctypes.byref(lim),ctypes.sizeof(lim)):
        k.CloseHandle(job)
        raise ctypes.WinError(ctypes.get_last_error())
    peak = 0
    stop = None
    started = time.monotonic()
    env = os.environ.copy()
    env.update({"TMP":str(scratch),"TEMP":str(scratch),"MPLCONFIGDIR":str(Path(scratch)/"mpl"),
                "OPENBLAS_NUM_THREADS":"1","OMP_NUM_THREADS":"1","PYTHONNOUSERSITE":"1"})
    try:
        with open(log,"w",encoding="utf-8") as stream:
            p = subprocess.Popen(command,cwd=cwd,stdin=subprocess.PIPE,stdout=stream,stderr=subprocess.STDOUT,env=env,text=True)
            if not k.AssignProcessToJobObject(job,w.HANDLE(int(p._handle))):
                p.kill();p.wait()
                raise ctypes.WinError(ctypes.get_last_error())
            p.stdin.write("START\n");p.stdin.flush();p.stdin.close()
            last_disk = 0
            while p.poll() is None:
                peak = max(peak,job_peak_rss(job))
                now = time.monotonic()
                if now-started > seconds:
                    stop = "RESOURCE_BLOCKED_WALL"
                if peak > 2*GIB:
                    stop = "RESOURCE_BLOCKED_RSS"
                if now-last_disk > 5:
                    if directory_bytes(scratch) > 2*GIB:
                        stop = "RESOURCE_BLOCKED_DISK"
                    last_disk = now
                if stop:
                    p.kill();p.wait();break
                time.sleep(.1)
            mem = Memory();mem.cb=ctypes.sizeof(mem)
            if getmem(w.HANDLE(int(p._handle)),ctypes.byref(mem),mem.cb):
                peak=max(peak,int(mem.peakws))
            return {"exit_code":p.returncode,"wall_seconds":time.monotonic()-started,
                    "peak_RSS_bytes":peak,"resource_stop":stop,"job_commit_limit_bytes":2*GIB,
                    "RSS_method":"maximum polled sum of job-member PeakWorkingSetSize;0.1s polling;commit capped separately"}
    finally:
        k.CloseHandle(job)
