"""Check the committed file manifest, metadata and GitHub file-size limits."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def verify():
    count=0
    for line in (ROOT/'MANIFEST.sha256').read_text().splitlines():
        expected,name=line.split('  ',1);path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT):raise ValueError('Unsafe manifest path')
        with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=expected:raise ValueError('Checksum mismatch: '+name)
        if path.stat().st_size>=25*1024*1024:raise ValueError('Exceeds browser upload size: '+name)
        count+=1
    meta=json.loads((ROOT/'.zenodo.json').read_text())
    assert 'metadata' not in meta and meta['upload_type']=='software'
    assert len(meta['creators'])==2 and meta['version']=='1.0.0'
    assert (ROOT/'CITATION.cff').read_text().startswith('cff-version: 1.2.0')
    print('PASS:',count,'files verified; file sizes and Zenodo metadata structure checked.')
if __name__=='__main__':verify()
