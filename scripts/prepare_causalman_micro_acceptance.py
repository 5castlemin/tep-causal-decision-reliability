"""Retrieve only pinned official micro software assets. Never import/unpickle them.

Run with --workspace OUTSIDE_REPO. It does not install the full CausalMan wheel
and does not grant data rights. Read CONTRACT.json rights/resource gates first.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import threading
import time
import urllib.request
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.causalman_micro_acceptance import PIN, TREE, GIB, verify_manifest_tree

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace",type=Path,required=True)
    args=ap.parse_args()
    root=args.workspace.resolve()
    repo=Path(__file__).resolve().parents[1]
    if root.is_relative_to(repo) or (root/"source").exists():
        raise ValueError("Fresh external source directory required")
    if shutil.disk_usage(root.parent).free < 2*GIB:
        raise RuntimeError("RESOURCE_BLOCKED_DISK")
    root.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();lock=threading.Lock();budget=[0]
    def fetch(url,limit):
        if time.monotonic()-started>=1800:
            raise RuntimeError("RESOURCE_BLOCKED_WALL")
        req=urllib.request.Request(url,headers={"User-Agent":"CausalMan-Micro-Contract-Acceptance"})
        with urllib.request.urlopen(req,timeout=90) as r:
            b=r.read(limit+1)
        if len(b)>limit:raise RuntimeError("DOWNLOAD_FILE_BOUND")
        with lock:
            budget[0]+=len(b)
            if budget[0]>GIB:raise RuntimeError("RESOURCE_BLOCKED_DOWNLOAD")
        return b
    base="https://api.github.com/repos/boschresearch/CausalMan/git/"
    commit=json.loads(fetch(base+"commits/"+PIN,200000))
    if commit["sha"]!=PIN or commit["tree"]["sha"]!=TREE:
        raise ValueError("SOURCE_IDENTITY_MISMATCH")
    tree=json.loads(fetch(base+"trees/"+TREE+"?recursive=1",8000000))
    selected=[v for v in tree["tree"] if v["type"]=="blob" and (
        v["path"].startswith("causalman/dataset_objects/causalman_micro/") or
        (v["path"].startswith("causalman/") and v["path"].endswith(".py") and "/dataset_objects/" not in v["path"]) or
        v["path"] in {"LICENSE","3rd-party-licenses.txt","README.md","pyproject.toml","requirements.txt","causalman/dataset_objects/__init__.py"})]
    micro=[v for v in selected if v["path"].startswith("causalman/dataset_objects/causalman_micro/")]
    if len(micro)!=1018 or sum(v["size"] for v in micro)!=144812833:
        raise ValueError("MICRO_MANIFEST_MISMATCH")
    provisional={"tree":TREE,"files":[{"path":v["path"],"git_blob_sha1":v["sha"]} for v in selected]}
    verify_manifest_tree(provisional,tree)
    def one(v):
        path=PurePosixPath(v["path"])
        if path.is_absolute() or ".." in path.parts or v["mode"]!="100644":
            raise ValueError("UNSAFE_ASSET_PATH")
        url="https://raw.githubusercontent.com/boschresearch/CausalMan/"+PIN+"/"+v["path"]
        b=fetch(url,v["size"])
        blob=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
        if len(b)!=v["size"] or blob!=v["sha"]:raise ValueError("ASSET_HASH_MISMATCH")
        dest=root/"source"/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
        return {"path":v["path"],"url":url,"bytes":len(b),"git_blob_sha1":blob,"sha256":hashlib.sha256(b).hexdigest()}
    records=[]
    try:
        with cf.ThreadPoolExecutor(max_workers=6) as pool:
            for result in pool.map(one,selected):records.append(result)
    finally:
        receipt={"status":"DOWNLOADED_HASH_VERIFIED_NOT_LOADED" if len(records)==len(selected) else "INCOMPLETE_NO_LOAD",
                 "commit":PIN,"tree":TREE,"files":sorted(records,key=lambda x:x["path"]),
                 "download_bytes":budget[0],"seconds":time.monotonic()-started}
        (root/"acquisition.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
        (root/"tree.json").write_text(json.dumps(tree),encoding="utf-8")
        (root/"commit.json").write_text(json.dumps(commit),encoding="utf-8")
    print(json.dumps({k:v for k,v in receipt.items() if k!="files"},indent=2))

if __name__=="__main__":
    main()
