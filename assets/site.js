// Artwork is published from Pages CMS into content/artwork and compiled to assets/artwork.json.
(async function(){
  let data=[];
  try {const r=await fetch('assets/artwork.json',{cache:'no-store'});if(!r.ok)throw Error('No artwork manifest');data=await r.json();}catch(e){return;}
  const escapeText=s=>String(s??'');
  const slug=document.body.dataset.category;
  if(slug){
    const gallery=document.querySelector('.gallery');
    const art=data.filter(x=>x.category===slug && x.image).sort((a,b)=>{const n=x=>x.order===''||x.order==null?999999:Number(x.order);return n(a)-n(b)||String(a.title).localeCompare(String(b.title))});
    if(gallery){gallery.replaceChildren();
      if(!art.length){const empty=document.createElement('p');empty.className='gallery-empty';empty.textContent='Artwork will appear here as it is added.';gallery.append(empty)}
      // Stable, varied neon color per artwork (does not change on refresh).
      const palette=['#ff29b4','#08e8f4','#ff851a','#f5f323','#a435ff'];
      art.forEach((x,index)=>{const b=document.createElement('button');
        const seed=String(x.title||'')+'|'+String(x.image||'');
        let hash=2166136261;
        for(let j=0;j<seed.length;j++){hash=Math.imul(hash^seed.charCodeAt(j),16777619)}
        b.style.setProperty('--art-color',palette[((hash>>>0)+index)%palette.length]);b.className='art';b.type='button';b.dataset.full=x.image;b.dataset.title=x.title;b.dataset.year=x.year||'';b.dataset.medium=x.medium||'';b.dataset.dimensions=x.dimensions||'';b.dataset.description=/^description goes here\.?$/i.test(String(x.description||'').trim())?'':(x.description||'');b.dataset.printUrl=x.print_url||'';b.dataset.additionalImages=JSON.stringify(x.additional_images||[]);
        const im=document.createElement('img');im.src=x.image;im.alt=x.title;im.loading='lazy';
        const info=document.createElement('div');info.className='info';const title=document.createElement('strong');title.textContent=x.title;
        const details=document.createElement('small');details.textContent=[x.medium,x.dimensions,x.year].filter(Boolean).join(' · ');
        info.append(title,details);b.append(im,info);gallery.append(b)});
      if(typeof window.setupArtworkMasonry==='function')window.setupArtworkMasonry(gallery);
      if(typeof window.setupArtworkLightbox==='function')window.setupArtworkLightbox();
    }
  }
})();

function setupArtworkLightbox(){
 const lb=document.querySelector('.lightbox');if(!lb)return;
 const items=[...document.querySelectorAll('.gallery [data-full]')];if(!items.length)return;
 const large=lb.querySelector('#large'),caption=lb.querySelector('#caption');
 const prev=lb.querySelector('.prev'),next=lb.querySelector('.next'),closeBtn=lb.querySelector('.close');
 let i=0,photoIndex=0,previousFocus=null,touchStart=null;
 const photoNav=document.createElement('div');photoNav.className='artwork-photo-nav';large.insertAdjacentElement('afterend',photoNav);
 function photos(){const item=items[i];let extras=[];try{extras=JSON.parse(item.dataset.additionalImages||'[]')}catch(e){}return [item.dataset.full,...extras].filter(Boolean)}
 function showPhoto(){const all=photos();photoIndex=Math.max(0,Math.min(photoIndex,all.length-1));large.src=all[photoIndex];photoNav.replaceChildren();photoNav.hidden=all.length<2;if(all.length<2)return;const bar=document.createElement('div');bar.className='artwork-photo-controls';const left=document.createElement('button');left.type='button';left.textContent='‹';left.setAttribute('aria-label','Previous photo');const count=document.createElement('span');count.textContent=(photoIndex+1)+' / '+all.length;const right=document.createElement('button');right.type='button';right.textContent='›';right.setAttribute('aria-label','Next photo');left.onclick=()=>changePhoto(-1);right.onclick=()=>changePhoto(1);bar.append(left,count,right);photoNav.append(bar);const strip=document.createElement('div');strip.className='artwork-photo-thumbs';all.forEach((src,n)=>{const b=document.createElement('button');b.type='button';b.className=n===photoIndex?'selected':'';b.setAttribute('aria-label','View photo '+(n+1));const im=document.createElement('img');im.src=src;im.alt='';im.loading='lazy';b.append(im);b.onclick=()=>{photoIndex=n;showPhoto()};strip.append(b)});photoNav.append(strip)}
 function changePhoto(step){const all=photos();if(all.length<2)return;photoIndex=(photoIndex+step+all.length)%all.length;showPhoto()}
 const siblings=[...lb.parentElement.children].filter(el=>el!==lb);
 const setBackgroundInert=active=>{siblings.forEach(el=>el.toggleAttribute('inert',active));document.querySelector('header')?.toggleAttribute('inert',active);document.querySelector('footer')?.toggleAttribute('inert',active)};
 function positionMobileArrows(){
  if(!lb.classList.contains('open'))return;
  const rect=large.getBoundingClientRect();
  if(rect.height>0)lb.style.setProperty('--artwork-image-mid',Math.round(rect.top+rect.height/2)+'px');
 }
 large.addEventListener('load',()=>requestAnimationFrame(positionMobileArrows));
 window.addEventListener('resize',positionMobileArrows);


 const category=(document.body.dataset.category||'artwork').replaceAll('-',' ');
 lb.setAttribute('aria-modal','true');lb.setAttribute('tabindex','-1');lb.setAttribute('aria-labelledby','artwork-dialog-title');
 function show(){
  const item=items[i];large.alt=item.dataset.title||'Artwork';showPhoto();caption.replaceChildren();
  const label=document.createElement('span');label.className='artwork-category';label.textContent=category+' / Artwork';caption.append(label);
  const title=document.createElement('strong');title.textContent=item.dataset.title||'Untitled';title.id='artwork-dialog-title';caption.append(title);
  const meta=[item.dataset.medium,item.dataset.dimensions,item.dataset.year].filter(Boolean);
  if(meta.length){const m=document.createElement('span');m.className='caption-meta';meta.forEach(value=>{const line=document.createElement('span');line.style.display='block';line.textContent=value;m.append(line)});caption.append(m)}
  if(item.dataset.description){
   const d=document.createElement('span');d.className='caption-description';
   const desc=item.dataset.description;const linkPattern=/\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)/g;let pos=0,match;
   while((match=linkPattern.exec(desc))!==null){
    d.append(document.createTextNode(desc.slice(pos,match.index)));
    try{const url=new URL(match[2]);if(url.protocol==='http:'||url.protocol==='https:'){
      const a=document.createElement('a');a.href=url.href;a.target='_blank';a.rel='noopener noreferrer';a.textContent=match[1];d.append(a);
    }else d.append(document.createTextNode(match[0]));}
    catch(e){d.append(document.createTextNode(match[0]));}
    pos=linkPattern.lastIndex;
   }
   d.append(document.createTextNode(desc.slice(pos)));caption.append(d);
  }
  const url=item.dataset.printUrl||'';
  if(/^https?:\/\//i.test(url)){
   const buy=document.createElement('a');buy.className='artwork-print-link';buy.href=url;buy.target='_blank';buy.rel='noopener noreferrer';buy.textContent='Buy a print';buy.setAttribute('aria-label','Buy a print of '+(item.dataset.title||'this artwork')+' (opens new tab)');caption.append(buy);
  }
  const count=document.createElement('span');count.className='caption-count';count.textContent=(i+1)+' / '+items.length;caption.append(count);
 }
 function open(n){previousFocus=document.activeElement;i=n;photoIndex=0;show();lb.classList.add('open');document.body.classList.add('artwork-viewer-open');setBackgroundInert(true);requestAnimationFrame(positionMobileArrows);closeBtn.focus()}
 function close(){lb.classList.remove('open');document.body.classList.remove('artwork-viewer-open');setBackgroundInert(false);large.removeAttribute('src');if(previousFocus&&previousFocus.focus)previousFocus.focus()}
 function move(n){i=(i+n+items.length)%items.length;photoIndex=0;show();requestAnimationFrame(positionMobileArrows)}
 // Deep-link to an individual artwork from the homepage featured card.
 // The gallery remains available when the viewer is closed.
 function openFromHash(){
  const prefix='#artwork=';
  if(!location.hash.startsWith(prefix))return;
  let requested='';
  try{requested=decodeURIComponent(location.hash.slice(prefix.length))}catch(e){return}
  const index=items.findIndex(el=>el.dataset.full.replace(/^\/+/, '')===requested.replace(/^\/+/, ''));
  if(index>=0&&!lb.classList.contains('open'))open(index);
 }
 items.forEach((el,n)=>el.addEventListener('click',()=>open(n)));
 window.addEventListener('hashchange',openFromHash);
 openFromHash();
 closeBtn.addEventListener('click',close);prev.addEventListener('click',()=>move(-1));next.addEventListener('click',()=>move(1));
 lb.addEventListener('click',e=>{if(e.target===lb)close()});
 document.addEventListener('keydown',e=>{
  if(!lb.classList.contains('open'))return;
  if(e.key==='Escape'){e.preventDefault();close()}
  if(e.key==='ArrowRight'){e.preventDefault();photos().length>1?changePhoto(1):move(1)}
  if(e.key==='ArrowLeft'){e.preventDefault();photos().length>1?changePhoto(-1):move(-1)}
  if(e.key==='Tab'){
   const focusable=[...lb.querySelectorAll('button,a[href]')].filter(x=>x.getClientRects().length);
   const first=focusable[0],last=focusable[focusable.length-1];
   if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}
   else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
  }
 });
 lb.addEventListener('touchstart',e=>{if(e.touches.length===1)touchStart={x:e.touches[0].clientX,y:e.touches[0].clientY}},{passive:true});
 lb.addEventListener('touchend',e=>{if(!touchStart||!lb.classList.contains('open'))return;const dx=e.changedTouches[0].clientX-touchStart.x,dy=e.changedTouches[0].clientY-touchStart.y;touchStart=null;if(Math.abs(dx)>65&&Math.abs(dx)>Math.abs(dy)*1.4)(photos().length>1?changePhoto(dx<0?1:-1):move(dx<0?1:-1))},{passive:true});
}
// Highlight the current navigation destination.
document.querySelectorAll('nav a').forEach(link=>{
 const target=new URL(link.href,location.href);
 const current=location.pathname.split('/').pop()||'index.html';
 const dest=target.pathname.split('/').pop();
 if(target.origin===location.origin && dest===current && !target.hash){
   link.setAttribute('aria-current','page');
 }
});

/* Pixel-precise masonry: 20px vertical and horizontal gutters. */
function setupArtworkMasonry(gallery){
  if(!gallery)return;
  let raf=0;
  function layout(){
    cancelAnimationFrame(raf);
    raf=requestAnimationFrame(()=>{
      const cards=[...gallery.querySelectorAll('.art')];
      if(!cards.length)return;
      const columns=window.innerWidth<=600?1:window.innerWidth<=900?2:3;
      const gap=Math.max(0,parseFloat(getComputedStyle(gallery).getPropertyValue('--gallery-masonry-gap'))||20);
      const width=gallery.clientWidth;
      const cardWidth=(width-gap*(columns-1))/columns;
      const heights=Array(columns).fill(0);
      gallery.style.position='relative';
      cards.forEach((card,index)=>{
        const col=index%columns;
        card.style.position='absolute';
        card.style.width=cardWidth+'px';
        card.style.left=(col*(cardWidth+gap))+'px';
        card.style.top=heights[col]+'px';
        card.style.gridRowEnd='auto';
        heights[col]+=card.getBoundingClientRect().height+gap;
      });
      gallery.style.height=Math.max(0,Math.max(...heights)-gap)+'px';
    });
  }
  gallery.querySelectorAll('.art img').forEach(img=>{
    img.addEventListener('load',layout);
    img.addEventListener('error',layout);
  });
  window.addEventListener('resize',layout,{passive:true});
  if(window.ResizeObserver)new ResizeObserver(layout).observe(gallery.parentElement||gallery);
  document.fonts?.ready.then(layout);
  layout();
}

/* Gallery category links, available directly on each gallery page. */
function setupGalleryCategoryNavigation(){
 const current=document.body.dataset.category;
 if(!current)return;
 const pagehead=document.querySelector('.pagehead');
 const gallery=document.querySelector('.gallery');
 if(!pagehead||!gallery||document.querySelector('.gallery-category-nav'))return;
 const nav=document.createElement('nav');
 nav.className='gallery-category-nav wrap';
 nav.setAttribute('aria-label','Browse artwork galleries');
 const links=[['Portraits','portraits.html','portraits'],['Queer','queer.html','queer'],['Star Wars','star-wars.html','star-wars'],['Various','various.html','various']];
 for(const [label,href,slug] of links){
   const a=document.createElement('a');a.href=href;a.textContent=label;
   if(current===slug)a.setAttribute('aria-current','page');
   nav.append(a);
 }
 pagehead.insertAdjacentElement('afterend',nav);
 // Use the actual gallery boundaries, including any theme-level padding.
 // This keeps the two navigation rules aligned on every gallery and viewport.
 const alignNavigation=()=>{
   const rect=gallery.getBoundingClientRect();
   const style=getComputedStyle(gallery);
   const leftInset=parseFloat(style.paddingLeft)||0;
   const rightInset=parseFloat(style.paddingRight)||0;
   const left=rect.left+leftInset;
   const width=Math.max(0,rect.width-leftInset-rightInset);
   const parentLeft=nav.parentElement.getBoundingClientRect().left;
   nav.style.setProperty('width',width+'px','important');
   nav.style.setProperty('margin-left',(left-parentLeft)+'px','important');
   nav.style.setProperty('margin-right','0','important');
 };
 alignNavigation();
 window.addEventListener('resize',alignNavigation,{passive:true});
 if(window.ResizeObserver)new ResizeObserver(alignNavigation).observe(gallery);
}
setupGalleryCategoryNavigation();
