"""Stage a verified, minimal official model copy. Never overwrite existing paths."""
import argparse, hashlib, json, pathlib, zipfile

ROOT = pathlib.Path(__file__).resolve().parent

def sha(b):
    return hashlib.sha256(b).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--archive',type=pathlib.Path,required=True)
    ap.add_argument('--destination',type=pathlib.Path,required=True)
    args=ap.parse_args()
    manifest=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text(encoding='utf-8-sig'))
    if sha(args.archive.read_bytes()) != manifest['archive_sha256']:
        raise ValueError('official archive hash mismatch')
    if args.destination.exists():
        raise FileExistsError('destination must be a new directory')
    names=list(manifest['files']) + ['TEplot.m']
    with zipfile.ZipFile(args.archive) as archive:
        content={}
        for name in names:
            matches=[n for n in archive.namelist() if n=='temexd_mod/'+name]
            if len(matches)!=1:
                raise ValueError('missing or ambiguous member: '+name)
            content[name]=archive.read(matches[0])
            if name in manifest['files'] and sha(content[name])!=manifest['files'][name]:
                raise ValueError('file hash mismatch: '+name)
    args.destination.mkdir(parents=True)
    for name,blob in content.items():
        (args.destination/name).write_bytes(blob)
    print(json.dumps({'status':'STAGED_ONLY','files':{n:sha(b) for n,b in content.items()},'simulation':'NOT_RUN'},indent=2))

if __name__=='__main__':
    main()
