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
# Publish only web-sized artwork files. Originals remain in the source repository
# but the public dist/assets/uploads copies are overwritten at build time.
# Keeping the same URLs also protects artwork reused in other site sections.
try:
    from PIL import Image, ImageOps
except ImportError as exc:
    raise SystemExit('Pillow is required: add Pillow>=10,<13 to requirements.txt') from exc

MAX_ARTWORK_SIDE = 700
# Include images in gallery category subfolders even if they have not yet
# been assigned to a Pages CMS artwork entry. Preserve non-gallery assets,
# especially the full-width About collages and site branding.
GALLERY_FOLDERS = {'queer', 'queer art', 'portraits', 'star wars', 'star-wars',
                   'nintendo', 'miscellaneous', 'misc', 'other'}
uploads = ROOT / 'assets' / 'uploads'
category_images = set()
if uploads.exists():
    for source_file in uploads.rglob('*'):
        if not source_file.is_file():
            continue
        folder_parts = [part.lower() for part in source_file.relative_to(uploads).parts[:-1]]
        if any(part in GALLERY_FOLDERS for part in folder_parts):
            if source_file.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'):
                category_images.add(source_file.relative_to(ROOT).as_posix())
for relative in sorted({item['image'] for item in items} | category_images):
    source = ROOT / relative
    public = DIST / relative
    if not source.is_file():
        raise SystemExit(f'Artwork image not found: {relative}')
    if not public.is_file():
        raise SystemExit(f'Artwork image missing from output: {relative}')
    try:
        with Image.open(source) as original:
            if original.format not in ('JPEG', 'PNG', 'WEBP'):
                raise ValueError('Supported gallery formats: JPEG, PNG, WebP')
            image = ImageOps.exif_transpose(original)
            image.thumbnail((MAX_ARTWORK_SIDE, MAX_ARTWORK_SIDE), Image.Resampling.LANCZOS)
            fmt = original.format
            if fmt == 'JPEG':
                if image.mode not in ('RGB', 'L'):
                    image = image.convert('RGB')
                image.save(public, format='JPEG', quality=80, optimize=True, progressive=True, exif=b'')
            elif fmt == 'WEBP':
                image.save(public, format='WEBP', quality=80, method=6, exif=b'', icc_profile=b'')
            else:
                # Keep PNG transparency; never convert to a lossy JPEG.
                image.save(public, format='PNG', optimize=True)
    except Exception as exc:
        raise SystemExit(f'Unable to prepare gallery image {relative}: {exc}') from exc

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
    if not isinstance(obj,dict):return {}
    # Pages CMS stores the rich-text `body` field as Markdown after the
    # closing frontmatter delimiter, not as a YAML frontmatter property.
    # Preserve an explicit YAML body if one exists for older content.
    body_after_frontmatter=raw[m.end():].strip()
    if body_after_frontmatter and not obj.get('body'):
        obj['body']=body_after_frontmatter
    return obj

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
    # Single combined name graphic takes precedence over legacy split uploads.
    combined_name_img=safe_image(home.get('name_heading_image'))
    if combined_name_img:
        combined_markup='<h1 class="hero-name-combined" aria-label="Bry Sharland"><img src="'+escape(combined_name_img,quote=True)+'" alt="" loading="eager" decoding="async"></h1>'
        page=re.sub(r'<h1><b>BRY</b><em>Sharland</em></h1>',lambda m:combined_markup,page,count=1)
    # Independently uploaded heading graphics, retaining semantic text and a
    # text-only fallback until an image is supplied.
    bry_img=safe_image(home.get('bry_heading_image'))
    sharland_img=safe_image(home.get('sharland_heading_image'))
    if (bry_img or sharland_img) and not combined_name_img:
        def pct(name,default):
            try: return min(100,max(10,float(home.get(name) or default)))
            except (ValueError,TypeError):return default
        def px(name,default):
            try:return min(160,max(-80,float(home.get(name) if home.get(name) is not None else default)))
            except (ValueError,TypeError):return default
        alignment=str(home.get('heading_alignment') or 'left').lower()
        if alignment not in ('left','center','right'):alignment='left'
        def graphic(image,label,kind):
            if image:
                return '<span class="hero-name-line '+kind+'"><img src="'+escape(image,quote=True)+'" alt="" loading="eager" decoding="async"></span>'
            return '<span class="hero-name-line '+kind+' hero-name-text">'+escape(label)+'</span>'
        markup='<h1 class="hero-name-images" aria-label="Bry Sharland" style="'+            '--bry-desktop:'+str(pct('bry_width_desktop',85))+'%;'+            '--sharland-desktop:'+str(pct('sharland_width_desktop',95))+'%;'+            '--bry-mobile:'+str(pct('bry_width_mobile',100))+'%;'+            '--sharland-mobile:'+str(pct('sharland_width_mobile',100))+'%;'+            '--name-gap-desktop:'+str(px('heading_gap_desktop',0))+'px;'+            '--name-gap-mobile:'+str(px('heading_gap_mobile',0))+'px;'+            '--name-align:'+alignment+'">'+            graphic(bry_img,'BRY','bry')+graphic(sharland_img,'Sharland','sharland')+'</h1>'
        page=re.sub(r'<h1><b>BRY</b><em>Sharland</em></h1>',lambda m:markup,page,count=1)
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
        if field in ('hero_title','hero_subtitle') and (bry_img or sharland_img or combined_name_img):continue
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
    # Render CMS rich text; the About page may intentionally have no second heading.
    if slug == 'about':
        import bleach
        heading = val(obj, 'section_title').strip()
        body = str(obj.get('body') or '').strip()
        if re.search(r'<(?:p|ul|ol|strong|em|h[1-6]|div|br)\b', body, re.I):
            formatted = bleach.clean(body, tags=['p','br','strong','em','ul','ol','li','a','h3','blockquote'],
                                     attributes={'a':['href','title']}, protocols=['http','https','mailto'], strip=True)
        elif markdown:
            formatted = bleach.clean(markdown.markdown(body), tags=['p','br','strong','em','ul','ol','li','a','h3','blockquote'],
                                     attributes={'a':['href','title']}, protocols=['http','https','mailto'], strip=True)
        else:
            formatted = ''.join('<p>'+escape(part).replace('\n','<br>')+'</p>' for part in re.split(r'\n\s*\n', body) if part.strip())
        heading_markup = '<h2>'+escape(heading)+'</h2>' if heading else ''
        section = '<section class="copy wrap">'+heading_markup+'<div class="cms-body">'+formatted+'</div></section>'
        # Replace only the informational copy section, not the page heading or collage.
        page, replaced = re.subn(r'<section\s+class=["\']copy wrap["\'][^>]*>.*?</section>',
                                 lambda m: section, page, count=1, flags=re.S)
        if not replaced:
            raise SystemExit('About page template is missing its copy section; refusing to deploy stale placeholder.')
    elif obj.get('body'):
        import bleach
        body = str(obj['body'])
        if re.search(r'<(?:p|ul|ol|strong|em|h[1-6]|div|br)\b', body, re.I):
            formatted = bleach.clean(body, tags=['p','br','strong','em','ul','ol','li','a','h3','blockquote'],
                                     attributes={'a':['href','title']}, protocols=['http','https','mailto'], strip=True)
        elif markdown:
            formatted = bleach.clean(markdown.markdown(body), tags=['p','br','strong','em','ul','ol','li','a','h3','blockquote'],
                                     attributes={'a':['href','title']}, protocols=['http','https','mailto'], strip=True)
        else:
            formatted = ''.join('<p>'+escape(part).replace('\n','<br>')+'</p>' for part in re.split(r'\n\s*\n', body) if part.strip())
        page = re.sub(r'(<section class="copy wrap"><h2>.*?</h2>).*?(</section>)',
                      lambda m:m.group(1)+'<div class="cms-body">'+formatted+'</div>'+m.group(2), page, count=1, flags=re.S)
    extras=''
    if slug=='about':
        desktop=safe_image(obj.get('collage_desktop')) or 'assets/uploads/Bry-Site-About-Header-Image-Monitor.png'
        mobile=safe_image(obj.get('collage_mobile')) or 'assets/uploads/Bry-Site-About-Header-Image-Mobile.png'
        if desktop:
            mobile_source='<source media="(max-width: 700px)" srcset="'+escape(mobile,quote=True)+'">' if mobile else ''
            collage='<div class="bry-about-collage wrap"><picture>'+mobile_source+'<img src="'+escape(desktop,quote=True)+'" alt="Collage of Bry Sharland self-portraits and artwork" decoding="async"></picture></div>'
            page=page.replace('<section class="copy wrap">',collage+'<section class="copy wrap">',1)
            page=page.replace('</head>','<link rel="stylesheet" href="assets/about-collage.css"></head>',1)
    if slug=='contact':
        key=val(obj,'web3forms_access_key','e7d707fb-6527-4cb2-9d1d-f559d029fcb0').strip()
        if not re.fullmatch(r'[a-zA-Z0-9-]{20,80}',key):key=''
        intro=escape(val(obj,'form_intro','Interested in a commission, original artwork, collaboration, or just want to say hello? Send Bry a message.'))
        heading=escape(val(obj,'form_heading','SEND A MESSAGE'))
        social_heading='FOLLOW ME'
        topics=['Commission / Custom Artwork','Artwork Purchase','Exhibition / Collaboration','General Question']
        options=''.join('<option value="'+escape(t,quote=True)+'">'+escape(t)+'</option>' for t in topics)
        form='''<form class="bry-contact-form" action="https://api.web3forms.com/submit" method="POST">
          <input type="hidden" name="access_key" value="{key}">
          <input type="hidden" name="subject" value="New Message from Bry Sharland Website">
          <input type="checkbox" name="botcheck" class="bry-honeypot" tabindex="-1" autocomplete="off" aria-hidden="true">
          <div class="bry-form-grid"><label>Your name<input name="name" type="text" autocomplete="name" required maxlength="120"></label>
          <label>Email address<input name="email" type="email" autocomplete="email" required maxlength="254"></label></div>
          <label>What are you contacting Bry about?<select name="inquiry_type" required><option value="" selected disabled>Choose a subject</option>{options}</select></label>
          <label>Your message<textarea name="message" rows="7" required maxlength="10000" placeholder="Tell Bry a little about what you have in mind..."></textarea></label>
          <button class="bry-submit" type="submit">SEND MESSAGE <span aria-hidden="true">→</span></button>
          <p class="bry-form-status" role="status" aria-live="polite"></p>
          </form>'''.format(key=escape(key,quote=True),options=options) if key else '<p>Contact form setup is pending.</p>'
        socials=[]
        for label,field in [('DeviantArt','deviantart'),('Instagram','instagram'),('Bluesky','bluesky')]:
            url=safe_url(obj.get(field))
            if url:socials.append('<a class="bry-social" href="'+escape(url,quote=True)+'" target="_blank" rel="noopener noreferrer"><span>'+label+'</span><span aria-hidden="true">↗</span></a>')
        social_html='<div class="bry-socials"><h2>'+social_heading+'</h2><div class="bry-social-grid">'+''.join(socials)+'</div></div>' if socials else ''
        section='<section class="copy wrap bry-contact-content"><p class="bry-contact-intro">'+intro+'</p>'+social_html+'<div class="bry-contact-panel"><h2>'+heading+'</h2>'+form+'</div></section>'
        page=re.sub(r'<section class="copy wrap">.*?</section>',lambda m:section,page,count=1,flags=re.S)
        page=page.replace('</head>','<link rel="stylesheet" href="assets/contact.css"></head>',1)
        page=page.replace('</body>','<script src="assets/contact.js" defer></script></body>',1)
    if extras:
        page=page.replace('</section></main>',extras+'</section></main>',1)
    page=page.replace('</head>','<link rel="stylesheet" href="assets/cms-pages.css"></head>',1)
    target.write_text(page,encoding='utf-8')


# Storefront directory. Each entry is a separate Pages CMS collection item.
# An empty URL renders a Coming Soon card, never a broken checkout link.
store_entries=[]
for file in sorted((ROOT/'content/stores').glob('*.md')):
    raw=file.read_text(encoding='utf-8-sig')
    m=re.match(r'^---\s*\n(.*?)\n---(?:\s*\n|$)',raw,re.S)
    if not m:continue
    item=yaml.safe_load(m.group(1)) or {}
    if not isinstance(item,dict) or item.get('visible') is False:continue
    try:order=int(item.get('order') or 100)
    except (ValueError,TypeError):order=100
    store_entries.append((order,file.name,item))
store_entries.sort(key=lambda row:(row[0],row[1]))
store_page=DIST/'store.html'
if store_page.exists():
    page=store_page.read_text(encoding='utf-8')
    store_cfg=read_page('store')
    intro=str(store_cfg.get('body') or '').strip()
    # Existing Store description can still be edited in CMS.
    if intro:
        if markdown: intro_html=markdown.markdown(intro)
        else:intro_html=''.join('<p>'+escape(x)+'</p>' for x in re.split(r'\n\s*\n',intro) if x.strip())
        import bleach
        intro_html=bleach.clean(intro_html,tags=['p','strong','em','br','a'],attributes={'a':['href']},protocols=['https','http'],strip=True)
    else:
        intro_html='<p>Explore prints, original artwork, and collections from Bry Sharland.</p>'
    cards=[]
    for _,filename,item in store_entries:
        name=str(item.get('title') or '').strip()[:110]
        if not name:continue
        description=str(item.get('description') or '').strip()[:600]
        image=safe_image(item.get('image'))
        url=safe_url(item.get('url'))
        button=str(item.get('button_text') or 'VISIT STORE').strip()[:60]
        picture='<div class="bry-store-image"><img src="'+escape(image,quote=True)+'" alt="'+escape(name,quote=True)+' artwork" loading="lazy"></div>' if image else '<div class="bry-store-image bry-store-image-empty" aria-hidden="true"><span>ART BY BRY</span></div>'
        action='<a class="bry-store-button" href="'+escape(url,quote=True)+'" target="_blank" rel="noopener noreferrer">'+escape(button)+' <span aria-hidden="true">↗</span></a>' if url else '<span class="bry-store-coming">COMING SOON</span>'
        cards.append('<article class="bry-store-card">'+picture+'<div class="bry-store-card-content"><h2>'+escape(name)+'</h2>'+(('<p>'+escape(description)+'</p>') if description else '')+action+'</div></article>')
    if not cards:
        cards=['<p class="bry-store-empty">Storefronts will appear here once added in Pages CMS.</p>']
    section='<section class="bry-store-directory wrap" aria-label="Online stores"><div class="bry-store-intro">'+intro_html+'</div><div class="bry-store-grid">'+''.join(cards)+'</div></section>'
    page,count=re.subn(r'<section\s+class="copy wrap"[^>]*>.*?</section>',lambda m:section,page,count=1,flags=re.S)
    if count!=1:raise SystemExit('Store page template copy section missing; not overwriting the site.')
    page=page.replace('</head>','<link rel="stylesheet" href="assets/store-directory.css"></head>',1)
    store_page.write_text(page,encoding='utf-8')

# Global appearance and navigation, applied to every generated HTML page.
legacy=read_page('appearance')
appearance={**legacy,**read_page('global-appearance'),**read_page('navigation-footer')}
home_appearance=read_page('home-appearance')
gallery_appearance=read_page('gallery-appearance')
def hex_color(key):
    raw=str(appearance.get(key) or '').strip()
    return raw if re.fullmatch(r'#[0-9a-fA-F]{6}',raw) else None

def pixel(key,default,low,high):
    try:return max(low,min(high,int(appearance.get(key) or default)))
    except (TypeError,ValueError):return default

body_fonts={'DM Sans':"'DM Sans',sans-serif",'Barlow Condensed':"'Barlow Condensed',sans-serif",
            'Oswald':"'Oswald',sans-serif",'Roboto Condensed':"'Roboto Condensed',sans-serif"}
heading_fonts={'Barlow Condensed':"'Barlow Condensed',sans-serif",'Anton':"'Anton',sans-serif",
               'Oswald':"'Oswald',sans-serif",'Bebas Neue':"'Bebas Neue',sans-serif",
               'Roboto Condensed':"'Roboto Condensed',sans-serif",'Archivo Black':"'Archivo Black',sans-serif"}
styles=[]
for key in ('pink','cyan','orange','yellow','purple'):
    color=hex_color(key)
    if color:styles.append('--'+key+':'+color+';')
background=hex_color('background_color')
foreground=hex_color('text_color')
if background:styles.append('--site-background:'+background+';')
if foreground:styles.append('--site-text:'+foreground+';')
body_font=body_fonts.get(appearance.get('body_font'))
heading_font=heading_fonts.get(appearance.get('heading_font'))
nav_font=body_fonts.get(appearance.get('navigation_font'))
if body_font:styles.append('--site-body-font:'+body_font+';')
if heading_font:styles.append('--site-heading-font:'+heading_font+';')
if nav_font:styles.append('--site-nav-font:'+nav_font+';')
if appearance.get('logo_width'):styles.append('--site-logo-width:'+str(pixel('logo_width',100,60,240))+'px;')

# Page-specific controls: scoped to the homepage or galleries.
def optional_px(obj,key,lo,hi):
    if obj.get(key) is None:return None
    try:return max(lo,min(hi,int(obj[key])))
    except (ValueError,TypeError):return None
def optional_percent(obj,key,lo,hi):
    return optional_px(obj,key,lo,hi)
page_rules=[]
def add_rule(selector,properties):
    if properties:page_rules.append(selector+'{'+''.join(properties)+'}')
p=[]
for key,prop,lo,hi in [('hero_min_height','min-height',250,1200)]:
    v=optional_px(home_appearance,key,lo,hi)
    if v is not None:p.append(prop+':'+str(v)+'px;')
add_rule('body:has(.hero) .hero',p)
p=[]
v=optional_percent(home_appearance,'hero_image_width',20,100)
if v is not None:p.append('width:'+str(v)+'%;')
v=optional_percent(home_appearance,'hero_image_position',0,100)
if v is not None:p.append('object-position:'+str(v)+'% center;')
add_rule('body:has(.hero) .hero>img',p)
v=optional_px(home_appearance,'section_spacing',20,180)
if v is not None:add_rule('body:has(.hero) .section',['padding-top:'+str(v)+'px;','padding-bottom:'+str(v)+'px;'])
v=optional_px(home_appearance,'slogan_font_size',16,90)
if v is not None:add_rule('body:has(.hero) .slogan',['font-size:'+str(v)+'px;'])
mobile=[]
v=optional_px(home_appearance,'hero_min_height_mobile',220,1100)
if v is not None:mobile.append('.hero{min-height:'+str(v)+'px;}')
v=optional_px(home_appearance,'slogan_font_size_mobile',16,80)
if v is not None:mobile.append('.slogan{font-size:'+str(v)+'px;}')
if mobile:page_rules.append('@media(max-width:700px){'+''.join('body:has(.hero) '+rule for rule in mobile)+'}')
v=optional_px(gallery_appearance,'gallery_gap',0,100)
if v is not None:add_rule('.gallery',['column-gap:'+str(v)+'px;'])
v=optional_px(gallery_appearance,'gallery_row_gap',0,140)
if v is not None:add_rule('.gallery',['row-gap:'+str(v)+'px!important;'])
v=optional_px(gallery_appearance,'caption_font_size',10,30)
if v is not None:add_rule('.gallery .art .info',['font-size:'+str(v)+'px;'])
color=str(gallery_appearance.get('caption_background') or '').strip()
if re.fullmatch(r'#[0-9a-fA-F]{6}',color):
    add_rule('.gallery .art .info',['background:'+color+'!important;'])
v=optional_px(gallery_appearance,'gallery_border_width',0,12)
if v is not None:add_rule('.gallery .art .info',['border-bottom-width:'+str(v)+'px!important;'])

if styles:
    (DIST/'assets/appearance.css').write_text(':root{'+''.join(styles)+'}\n'+'\n'.join(page_rules),encoding='utf-8')
else:
    (DIST/'assets/appearance.css').write_text('/* Defaults unchanged */\n'+'\n'.join(page_rules),encoding='utf-8')

for target in DIST.glob('*.html'):
    page=target.read_text(encoding='utf-8')
    page=page.replace('</head>','<link rel="stylesheet" href="assets/cms-pages.css"><link rel="stylesheet" href="assets/appearance.css"></head>',1) if 'assets/cms-pages.css' not in page else page.replace('</head>','<link rel="stylesheet" href="assets/appearance.css"></head>',1)
    logo=safe_image(appearance.get('logo_image'))
    if logo:
        page=re.sub(r'(<header>.*?<img class="logo" src=")[^"]*(")',lambda m:m.group(1)+escape(logo,quote=True)+m.group(2),page,count=1,flags=re.S)
    nav_labels={'nav_home':'index.html','nav_artwork':'index.html#work','nav_about':'about.html','nav_contact':'contact.html','nav_store':'store.html'}
    for key,href in nav_labels.items():
        if appearance.get(key):
            pattern=r'(<nav\b[^>]*>.*?<a href="'+re.escape(href)+r'"[^>]*>).*?(</a>)'
            page=re.sub(pattern,lambda m:m.group(1)+escape(str(appearance[key])[:45])+m.group(2),page,count=1,flags=re.S)
    site_name=str(appearance.get('site_name') or '').strip()
    if site_name:
        page=re.sub(r'<title>(.*?)</title>',lambda m:'<title>'+escape(m.group(1).split(' | ')[0]+' | '+site_name[:80])+'</title>',page,count=1)
    if appearance.get('footer_text'):
        page=re.sub(r'(<footer\b[^>]*>.*?<div class="wrap">).*?(</div>)',lambda m:m.group(1)+escape(str(appearance['footer_text'])[:250])+m.group(2),page,count=1,flags=re.S)
    # Page-level typography controls, independent of the global theme.
    slug=target.stem
    cfg=read_page(slug) if slug in ('about','contact','store') else (read_page('home') if slug=='index' else {})
    if slug in ('queer','portraits','star-wars','nintendo','miscellaneous'):
        cfg=read_page('unused')
        gp=ROOT/'content/gallery-pages'/(slug+'.md')
        if gp.exists():
            m=re.match(r'^---\s*\n(.*?)\n---(?:\s*\n|$)',gp.read_text(encoding='utf-8-sig'),re.S)
            if m:
                data=yaml.safe_load(m.group(1)) or {}
                if isinstance(data,dict):cfg=data
    def color_setting(key):
        return allowed_colors.get(str(cfg.get(key) or '').lower())
    def font_setting(key):
        return allowed_fonts.get(str(cfg.get(key) or ''))
    def size_setting(key,lo=10,hi=180):
        try:return str(max(lo,min(hi,int(cfg[key]))))+'px' if cfg.get(key) is not None else None
        except (ValueError,TypeError):return None
    def cssprops(spec):
        return ';'.join('--'+prop+':'+str(value) for prop,value in spec.items() if value is not None)
    if slug!='index':
        # Set variables on the page heading container, so existing inline gallery title settings still work.
        props=cssprops({'eyebrow-custom-color':color_setting('eyebrow_color'),
          'eyebrow-custom-font':font_setting('eyebrow_font'),
          'eyebrow-custom-size':size_setting('eyebrow_size',10,48),
          'heading-color':color_setting('title_color'),
          'heading-shadow':color_setting('shadow_color'),
          'heading-font':font_setting('title_font'),
          'heading-size':size_setting('title_size',48,180),
          'section-custom-color':color_setting('section_color'),
          'section-custom-shadow':color_setting('section_shadow_color'),
          'section-custom-font':font_setting('section_font'),
          'section-custom-size':size_setting('section_size',20,100)})
        if props:
            page=page.replace('<body','<body style="'+escape(props,quote=True)+'"',1)
        # Section headings must get their own text labels for the offset effect.
        def add_section_label(m):
            attrs,content=m.group(1),m.group(2)
            label=html.unescape(re.sub(r'<[^>]+>','',content)).strip()
            return '<h2'+attrs+' data-shadow-text="'+escape(label,quote=True)+'">'+content+'</h2>'
        page=re.sub(r'<h2([^>]*)>(.*?)</h2>',add_section_label,page,flags=re.S)
    else:
        props=cssprops({'eyebrow-custom-color':color_setting('eyebrow_color'),
          'eyebrow-custom-size':size_setting('eyebrow_size',10,48),
          'home-work-color':color_setting('work_heading_color'),
          'home-work-shadow':color_setting('work_heading_shadow'),
          'home-work-size':size_setting('work_heading_size',20,110),
          'home-feature-color':color_setting('feature_heading_color'),
          'home-feature-shadow':color_setting('feature_heading_shadow'),
          'home-feature-size':size_setting('feature_heading_size',20,110)})
        if props:page=page.replace('<body','<body style="'+escape(props,quote=True)+'"',1)
    # Single editable brush-font introduction, preserving the existing neon title.
    intro_defaults={
      'about':'MEET THE ARTIST',
      'contact':"LET'S CONNECT",
      'store':'SHOP THE ART',
      'queer':'EXPLORE QUEER ART',
      'portraits':'EXPLORE PORTRAITS',
      'star-wars':'EXPLORE STAR WARS',
      'nintendo':'EXPLORE NINTENDO',
      'miscellaneous':'EXPLORE MORE ART',
    }
    if slug in intro_defaults:
        intro=intro_defaults[slug]
        if 'intro_brush' in cfg:
            intro=str(cfg.get('intro_brush') or '').strip()[:100]
        if intro:
            intro_color=allowed_colors.get(str(cfg.get('intro_brush_color') or 'pink').lower(),allowed_colors['pink'])
            label='<div class="bry-page-intro" style="--bry-intro-color:'+intro_color+'">'+escape(intro)+'</div>'
            page=re.sub(r'(<section class="pagehead wrap">)\s*<div class="eyebrow">.*?</div>',lambda m:m.group(1)+label,page,count=1,flags=re.S)
        else:
            page=re.sub(r'(<section class="pagehead wrap">)\s*<div class="eyebrow">.*?</div>',r'\1',page,count=1,flags=re.S)
        page=page.replace('</head>','<link rel="stylesheet" href="assets/page-intro-labels.css"></head>',1)
    # Restore layered headings for all gallery and ordinary pages, including CMS-edited titles.
    def heading_text(match):
        attrs, content = match.group(1), match.group(2)
        if 'data-shadow-text=' not in attrs:
            label=html.unescape(re.sub(r'<[^>]+>', '', content)).strip()
            attrs += ' data-shadow-text="'+escape(label,quote=True)+'"'
        return '<h1'+attrs+'>'+content+'</h1>'
    page=re.sub(r'<h1([^>]*)>(.*?)</h1>', heading_text, page, count=1, flags=re.S) if 'class="pagehead wrap"' in page else page
    page=page.replace('</head>','<link rel="stylesheet" href="assets/heading-restoration.css"><link rel="stylesheet" href="assets/page-heading-controls.css"></head>',1)
    layout_values = [pixel('content_padding_desktop',60,0,180), pixel('content_padding_tablet',32,0,120), pixel('content_padding_mobile',20,0,80)]
    layout_vars = ';'.join('--layout-side-'+key+':'+str(val)+'px' for key,val in zip(('desktop','tablet','mobile'),layout_values))
    page=page.replace('</head>','<style>:root{'+layout_vars+'}</style><link rel="stylesheet" href="assets/layout-spacing.css"><link rel="stylesheet" href="assets/homepage-refinements.css"><link rel="stylesheet" href="assets/store-home-fixes.css"></head>',1)
    if slug=='contact':
        page=page.replace('</head>','<link rel="stylesheet" href="assets/global-socials.css"></head>',1)
    # Shared social links: use Contact Page CMS values across the website.
    # Contact already displays these links above its form, so avoid duplication.
    if slug != 'contact' and '<footer' in page:
        social_settings=read_page('contact')
        social_defaults={
            'deviantart':'https://www.deviantart.com/brysharland',
            'instagram':'https://www.instagram.com/brysharlandart/',
            'bluesky':'https://bsky.app/profile/brysharlandart.bsky.social',
        }
        social_buttons=[]
        for label,field in [('DeviantArt','deviantart'),('Instagram','instagram'),('Bluesky','bluesky')]:
            # An explicitly blank field hides the corresponding button.
            raw_url=social_settings.get(field,social_defaults[field])
            url=safe_url(raw_url)
            if url:
                social_buttons.append('<a class="bry-global-social" href="'+escape(url,quote=True)+'" target="_blank" rel="noopener noreferrer"><span>'+label+'</span><span aria-hidden="true">↗</span></a>')
        if social_buttons:
            socials_markup='<section class="bry-global-socials wrap" aria-label="Bry Sharland social media"><h2>FOLLOW ME</h2><div class="bry-global-social-grid">'+''.join(social_buttons)+'</div></section>'
            page=page.replace('<footer',socials_markup+'<footer',1)
            page=page.replace('</head>','<link rel="stylesheet" href="assets/global-socials.css"></head>',1)
    target.write_text(page,encoding='utf-8')

print(f'Built {len(items)} artwork entries into dist/')


# Interior-page hero/content separation (homepage and About deliberately excluded).
# Move the contact/store introductory copy into the heading area, then place a
# container-width divider between the page introduction and the main content.
for slug in ('contact','store','queer','portraits','star-wars','nintendo','miscellaneous'):
    target=DIST/(slug+'.html')
    if not target.exists():continue
    page=target.read_text(encoding='utf-8')
    if slug=='contact':
        # The CMS contact intro belongs with the title, not the form/social area.
        m=re.search(r'<p class="bry-contact-intro">.*?</p>',page,re.S)
        if m:
            intro=m.group(0)
            page=page[:m.start()]+page[m.end():]
            page=page.replace('</section>',intro+'</section>',1) if '<section class="pagehead wrap">' in page else page
    elif slug=='store':
        # Move the optional CMS store introduction above the rule.
        m=re.search(r'<div class="bry-store-intro">.*?</div>',page,re.S)
        if m:
            intro=m.group(0)
            page=page[:m.start()]+page[m.end():]
            page=page.replace('</section>',intro+'</section>',1) if '<section class="pagehead wrap">' in page else page
    page,n=re.subn(r'(</section>)(\s*)(?=<(?:section|div)\b)',
       lambda m:m.group(1)+'<div class="bry-interior-divider wrap" aria-hidden="true"><span></span></div>'+m.group(2),
       page,count=1) if '<section class="pagehead wrap">' in page else (page,0)
    if n:
        page=page.replace('</head>','<link rel="stylesheet" href="assets/interior-divider.css"></head>',1)
    target.write_text(page,encoding='utf-8')

# Responsive site navigation. Add the same accessible mobile menu on every page
# without changing existing desktop links, page content, or navigation styling.
for target in DIST.glob('*.html'):
    page = target.read_text(encoding='utf-8')
    if 'assets/mobile-navigation.css' not in page:
        page = page.replace('</head>', '<link rel="stylesheet" href="assets/mobile-navigation.css"></head>', 1)
    if 'assets/mobile-navigation.js' not in page:
        page = page.replace('</body>', '<script src="assets/mobile-navigation.js" defer></script></body>', 1)
    target.write_text(page, encoding='utf-8')
