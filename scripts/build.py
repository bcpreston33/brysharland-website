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
    item['order']=obj.get('order','')
    items.append(item)
(DIST/'assets/artwork.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')

# Optional per-gallery heading settings from Pages CMS.
import html
settings_dir=ROOT/'content/gallery-pages'
allowed_colors={'orange':'#ff8618','pink':'#ff27ac','purple':'#a435ff','cyan':'#05dff2','yellow':'#fff023','white':'#ffffff'}
allowed_fonts={'Barlow Condensed':"'Barlow Condensed',sans-serif",
               'Anton':"'Anton',sans-serif",
               'Oswald':"'Oswald',sans-serif",
               'Bebas Neue':"'Bebas Neue',sans-serif",
               'Roboto Condensed':"'Roboto Condensed',sans-serif",
               'Archivo Black':"'Archivo Black',sans-serif",
               'Barlow Condensed Italic':"'Barlow Condensed',sans-serif",
               'Oswald Italic':"'Oswald',sans-serif",
               'Roboto Condensed Italic':"'Roboto Condensed',sans-serif"}
for slug in ('queer','portraits','star-wars','nintendo','miscellaneous'):
    target=DIST/(slug+'.html')
    if not target.exists():continue
    page=target.read_text(encoding='utf-8')
    setting_file=settings_dir/(slug+'.md')
    obj={}
    if setting_file.exists():
        raw=setting_file.read_text(encoding='utf-8-sig')
        match=re.match(r'^---\s*\n(.*?)\n---(?:\s*\n|$)',raw,re.S)
        if match:
            import yaml
            obj=yaml.safe_load(match.group(1)) or {}
            if not isinstance(obj,dict):obj={}
    defaults={'queer':'Queer','portraits':'Portraits','star-wars':'Star Wars','nintendo':'Nintendo','miscellaneous':'Miscellaneous'}
    title=str(obj.get('title') or defaults[slug])[:100]
    eyebrow=str(obj.get('eyebrow') or 'Artwork / '+defaults[slug])[:120]
    description=str(obj.get('description') or '')[:1200]
    color=allowed_colors.get(str(obj.get('title_color') or 'orange').lower(),allowed_colors['orange'])
    shadow=allowed_colors.get(str(obj.get('shadow_color') or 'cyan').lower(),allowed_colors['cyan'])
    font=allowed_fonts.get(str(obj.get('title_font') or 'Barlow Condensed'),allowed_fonts['Barlow Condensed'])
    try:size=max(48,min(180,int(obj.get('title_size') or 110)))
    except (ValueError,TypeError):size=110
    italic='italic' in str(obj.get('title_font') or '').lower()
    style=f'--heading-slant:{"italic" if italic else "normal"};--heading-color:{color};--heading-shadow:{shadow};--heading-font:{font};--heading-size:clamp(52px,10vw,{size}px)'
    head=f'<div class="eyebrow">{html.escape(eyebrow)}</div><h1 data-shadow-text="{html.escape(title,quote=True)}" style="{html.escape(style,quote=True)}">{html.escape(title)}</h1>'
    # Preserve existing description unless CMS explicitly provides one.
    if description:head+=f'<p>{html.escape(description)}</p>'
    else:
        old=re.search(r'<section class="pagehead wrap">.*?(<p>.*?</p>)</section>',page,re.S)
        if old:head+=old.group(1)
    page=re.sub(r'(<section class="pagehead wrap">).*?(</section>)',
                lambda m:m.group(1)+head+m.group(2),page,count=1,flags=re.S)
    target.write_text(page,encoding='utf-8')


# Edit ordinary site pages from Pages CMS without changing their original templates.
from urllib.parse import urlparse
from html import escape
import yaml

def read_page(slug):
    p=ROOT/'content/pages'/f'{slug}.md'
    if not p.exists():return {}
    raw=p.read_text(encoding='utf-8-sig')
