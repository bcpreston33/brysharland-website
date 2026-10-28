#!/usr/bin/env python3
"""Compile Pages CMS artwork entries into a safe static JSON manifest, then copy site to dist."""
import json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
DIST=ROOT/'dist'
if DIST.exists():shutil.rmtree(DIST)
DIST.mkdir()
for p in ROOT.glob('*.html'):shutil.copy2(p,DIST/p.name)
shutil.copytree(ROOT/'assets',DIST/'assets',ignore=shutil.ignore_patterns('artwork.json'))
items=[]
for p in sorted((ROOT/'content/artwork').glob('*.md')):
    raw=p.read_text(encoding='utf-8-sig')
    if not raw.startswith('---'):continue
    m=re.match(r'^---\s*\n(.*?)\n---(?:\s*\n|$)',raw,re.S)
    if not m:continue
    front=m.group(1)
    # Pages CMS outputs YAML. PyYAML is available in Cloudflare's Python build image only if installed.
    try:
        import yaml
    except ImportError as e:
        raise SystemExit('Install dependencies: pip install -r requirements.txt') from e
    obj=yaml.safe_load(front)
    if not isinstance(obj,dict):continue
    category_raw=str(obj.get('category','')).strip()
    category=re.sub(r'[^a-z0-9]+','-',category_raw.lower()).strip('-')
    if category not in ('queer','portraits','star-wars','nintendo','miscellaneous'):continue
    image=obj.get('image','')
    if not isinstance(image,str) or not image.startswith('/assets/uploads/') and not image.startswith('assets/uploads/'):
        continue
    image=image.lstrip('/')
    item={k:str(obj.get(k) or '') for k in ('title','category','year','medium','dimensions','description')}
    item['category']=category
    item['image']=image
    item['featured']=obj.get('featured') is True
    items.append(item)
(DIST/'assets/artwork.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Built {len(items)} artwork entries into dist/')
