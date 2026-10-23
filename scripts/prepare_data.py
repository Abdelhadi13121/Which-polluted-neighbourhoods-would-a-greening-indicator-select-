"""Restore exact CSV bytes from committed gzip parts using only Python stdlib."""
from pathlib import Path
import argparse,hashlib,json,zlib
ROOT=Path(__file__).resolve().parents[1]
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def restore(force=False):
    manifest=json.loads((ROOT/'data/manifest.json').read_text())
    for item in manifest['datasets']:
        target=ROOT/'data'/item['filename']
        if target.exists():
            if sha(target)==item['sha256']:
                print('Verified existing',target.name,flush=True);continue
            if not force:raise RuntimeError(f'{target.name} differs from the archived input; use --force to replace it with the verified source.')
        temp=target.with_suffix('.csv.restoring');dec=zlib.decompressobj(16+zlib.MAX_WBITS)
        output_hash=hashlib.sha256();archive_hash=hashlib.sha256();size=0
        try:
            with temp.open('wb') as dest:
                for part in item['parts']:
                    path=(ROOT/part['path']).resolve()
                    if not path.is_relative_to((ROOT/'data/archives').resolve()):raise ValueError('Unexpected archive path')
                    if path.stat().st_size!=part['bytes'] or sha(path)!=part['sha256']:raise ValueError('Part checksum mismatch: '+path.name)
                    with path.open('rb') as src:
                        while block:=src.read(65536):
                            archive_hash.update(block);data=dec.decompress(block);dest.write(data);output_hash.update(data);size+=len(data)
                data=dec.flush();dest.write(data);output_hash.update(data);size+=len(data)
            if not dec.eof or dec.unused_data:raise ValueError('Incomplete or unexpected gzip stream')
            if archive_hash.hexdigest()!=item['compressed_sha256']:raise ValueError('Compressed-stream checksum mismatch')
            if output_hash.hexdigest()!=item['sha256'] or size!=item['bytes']:raise ValueError('Restored CSV checksum mismatch')
            temp.replace(target);print('Restored and verified',target.name,size,'bytes',flush=True)
        finally:
            if temp.exists():temp.unlink()
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--force',action='store_true');restore(parser.parse_args().force)
