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
    m=re.match(r'^---\s*\n(.*?)\n---(?:\s*\n|$)',raw,re.S)
    if not m:return {}
    obj=yaml.safe_load(m.group(1)) or {}
    return obj if isinstance(obj,dict) else {}

def val(obj,key,default=''):
    v=obj.get(key)
    return str(v) if v is not None else default

def safe_image(v):
    s=str(v or '').lstrip('/')
    return '/'+s if s.startswith('assets/uploads/') or s.startswith('assets/featured-art.') else ''

def safe_url(v):
    s=str(v or '').strip()
    p=urlparse(s)
    return s if p.scheme in ('https','http') and p.netloc else ''

def sub(pattern, replacement, html_text):
    return re.sub(pattern,lambda m:replacement,html_text,count=1,flags=re.S)

home=read_page('home')
target=DIST/'index.html'
page=target.read_text(encoding='utf-8')
if home:
    # All fields optional; missing entries preserve existing homepage.
    img=safe_image(home.get('hero_image'))
    if img:
        page=sub(r'(<section class="hero"><img )src="[^"]*" alt="[^"]*"',
                 r'\1' if False else '<section class="hero"><img src="'+escape(img,quote=True)+'" alt="'+escape(val(home,'hero_alt','Artwork by Bry Sharland'),quote=True)+'"',page)
    mapping={
      'eyebrow':r'(<section class="hero">.*?<div class="eyebrow">).*?(</div>)',
      'hero_title':r'(<section class="hero">.*?<h1><b>).*?(</b>)',
      'hero_subtitle':r'(<section class="hero">.*?<h1><b>.*?</b><em>).*?(</em>)',
      'slogan_one':r'(<div class="slogan"><span>).*?(</span>)',
      'slogan_two':r'(<div class="slogan"><span>.*?</span><span>).*?(</span>)',
      'slogan_three':r'(<div class="slogan"><span>.*?</span><span>.*?</span><span>).*?(</span>)',
      'button_text':r'(<a class="btn" href="#work">).*?(</a>)',
      'work_heading':r'(<div class="section-title">).*?(<em>)',
      'work_heading_accent':r'(<div class="section-title">.*?<em>).*?(</em>)',
      'feature_eyebrow':r'(<section class="feature">.*?<div class="eyebrow">).*?(</div>)',
      'feature_title':r'(<section class="feature">.*?<h2>).*?(</h2>)',
      'feature_description':r'(<section class="feature">.*?<h2>.*?</h2><p>).*?(</p>)',
      'feature_button_text':r'(<section class="feature">.*?<a class="outline"[^>]*>).*?(</a>)'
    }
    for field,pattern in mapping.items():
        if field in home and home[field] is not None:
            content=escape(val(home,field))
            if field=='feature_title':content=content.replace('\n','<br>')
            page=re.sub(pattern,lambda m:m.group(1)+content+m.group(2),page,count=1,flags=re.S)
    if 'category_note' in home:
        note=val(home,'category_note')
        page=sub(r'<p class="note">.*?</p>',('<p class="note">'+escape(note)+'</p>') if note else '',page)
    category_images={'queer_image':'queer','portraits_image':'portraits','star_wars_image':'star-wars','nintendo_image':'nintendo','miscellaneous_image':'miscellaneous'}
    for field,slug in category_images.items():
        img=safe_image(home.get(field))
        if img:
            pattern=r'(<a class="tile" href="'+slug+r'\.html"><div class="photo"><img src=")[^"]*(")'
            page=re.sub(pattern,lambda m:m.group(1)+escape(img,quote=True)+m.group(2),page,count=1)
    url=safe_url(home.get('feature_url'))
    if url:
        page=re.sub(r'(<section class="feature">.*?<a class="outline" href=")[^"]*(")',lambda m:m.group(1)+escape(url,quote=True)+m.group(2),page,count=1,flags=re.S)
    img=safe_image(home.get('feature_image'))
    if img:
        page=sub(r'<div class="feature-art">.*?</div>', '<div class="feature-art"><img src="'+escape(img,quote=True)+'" alt="Featured project artwork"></div>',page)
page=page.replace('</head>','<link rel="stylesheet" href="assets/cms-pages.css"></head>',1)
target.write_text(page,encoding='utf-8')

# Static editable informational pages. Render rich-text conservatively using markdown.
try:
    import markdown
except ImportError:
    markdown=None

for slug in ('about','contact','store'):
    obj=read_page(slug)
    if not obj:continue
    target=DIST/(slug+'.html')
    page=target.read_text(encoding='utf-8')
    for field,pattern in {
        'eyebrow':r'(<section class="pagehead wrap"><div class="eyebrow">).*?(</div>)',
        'title':r'(<section class="pagehead wrap">.*?<h1>).*?(</h1>)',
        'section_title':r'(<section class="copy wrap"><h2>).*?(</h2>)'
    }.items():
        if field in obj and obj[field] is not None:
            page=re.sub(pattern,lambda m:m.group(1)+escape(val(obj,field))+m.group(2),page,count=1,flags=re.S)
    if obj.get('body'):
        body=str(obj['body'])
        # Pages CMS rich text may store HTML or Markdown. Sanitize with bleach.
        import bleach
        if '<p' in body or '<ul' in body or '<strong' in body:
            formatted=bleach.clean(body,tags=['p','br','strong','em','ul','ol','li','a','h3','blockquote'],attributes={'a':['href','title']},protocols=['http','https','mailto'],strip=True)
        else:
            formatted=bleach.clean(markdown.markdown(body) if markdown else '<p>'+escape(body)+'</p>',tags=['p','br','strong','em','ul','ol','li','a','h3','blockquote'],attributes={'a':['href','title']},protocols=['http','https','mailto'],strip=True)
        page=re.sub(r'(<section class="copy wrap"><h2>.*?</h2>).*?(</section>)',lambda m:m.group(1)+'<div class="cms-body">'+formatted+'</div>'+m.group(2),page,count=1,flags=re.S)
    extras=''
    if slug=='about':
        img=safe_image(obj.get('image'))
        if img:extras='<img class="cms-portrait" src="'+escape(img,quote=True)+'" alt="Bry Sharland">'
    if slug=='contact':
        email=val(obj,'email').strip()
        if re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email):
            extras+='<p><a href="mailto:'+escape(email,quote=True)+'">'+escape(email)+'</a></p>'
        instagram=safe_url(obj.get('instagram'))
        if instagram:extras+='<p><a href="'+escape(instagram,quote=True)+'" rel="noopener" target="_blank">Instagram ↗</a></p>'
    if slug=='store':
        store=safe_url(obj.get('store_url'))
        if store:extras+='<p><a class="btn" href="'+escape(store,quote=True)+'" rel="noopener" target="_blank">'+escape(val(obj,'button_text','Visit the store'))+'</a></p>'
    if extras:
        page=page.replace('</section></main>',extras+'</section></main>',1)
    page=page.replace('</head>','<link rel="stylesheet" href="assets/cms-pages.css"></head>',1)
    target.write_text(page,encoding='utf-8')

print(f'Built {len(items)} artwork entries into dist/')
