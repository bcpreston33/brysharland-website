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
        b.style.setProperty('--art-color',palette[((hash>>>0)+index)%palette.length]);b.className='art';b.type='button';b.dataset.full=x.image;b.dataset.title=x.title;b.dataset.year=x.year||'';b.dataset.medium=x.medium||'';b.dataset.dimensions=x.dimensions||'';b.dataset.description=/^description goes here\.?$/i.test(String(x.description||'').trim())?'':(x.description||'');b.dataset.printUrl=x.print_url||'';
        const im=document.createElement('img');im.src=x.image;im.alt=x.title;im.loading='lazy';
        const info=document.createElement('div');info.className='info';const title=document.createElement('strong');title.textContent=x.title;
        const details=document.createElement('small');details.textContent=[x.medium,x.dimensions,x.year].filter(Boolean).join(' · ');
        info.append(title,details);b.append(im,info);gallery.append(b)});
      if(typeof window.setupArtworkLightbox==='function')window.setupArtworkLightbox();
    }
  }
})();

function setupArtworkLightbox(){
 const lb=document.querySelector('.lightbox');if(!lb)return;
 const items=[...document.querySelectorAll('.gallery [data-full]')];if(!items.length)return;
 const large=lb.querySelector('#large'),caption=lb.querySelector('#caption');
 const prev=lb.querySelector('.prev'),next=lb.querySelector('.next'),closeBtn=lb.querySelector('.close');
 let i=0,previousFocus=null,touchStart=null;
 const category=(document.body.dataset.category||'artwork').replaceAll('-',' ');
 lb.setAttribute('aria-modal','true');lb.setAttribute('tabindex','-1');
 function show(){
  const item=items[i];large.src=item.dataset.full;large.alt=item.dataset.title||'Artwork';caption.replaceChildren();
  const label=document.createElement('span');label.className='artwork-category';label.textContent=category+' / Artwork';caption.append(label);
  const title=document.createElement('strong');title.textContent=item.dataset.title||'Untitled';caption.append(title);
  const meta=[item.dataset.medium,item.dataset.dimensions,item.dataset.year].filter(Boolean);
  if(meta.length){const m=document.createElement('span');m.className='caption-meta';meta.forEach(value=>{const line=document.createElement('span');line.style.display='block';line.textContent=value;m.append(line)});caption.append(m)}
  if(item.dataset.description){const d=document.createElement('span');d.className='caption-description';d.textContent=item.dataset.description;caption.append(d)}
  const url=item.dataset.printUrl||'';
  if(/^https?:\/\//i.test(url)){
   const buy=document.createElement('a');buy.className='artwork-print-link';buy.href=url;buy.target='_blank';buy.rel='noopener noreferrer';buy.textContent='Buy a print';buy.setAttribute('aria-label','Buy a print of '+(item.dataset.title||'this artwork')+' (opens new tab)');caption.append(buy);
  }
  const count=document.createElement('span');count.className='caption-count';count.textContent=(i+1)+' / '+items.length;caption.append(count);
 }
 function open(n){previousFocus=document.activeElement;i=n;show();lb.classList.add('open');document.body.classList.add('artwork-viewer-open');closeBtn.focus()}
 function close(){lb.classList.remove('open');document.body.classList.remove('artwork-viewer-open');large.removeAttribute('src');if(previousFocus&&previousFocus.focus)previousFocus.focus()}
 function move(n){i=(i+n+items.length)%items.length;show()}
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
  if(e.key==='ArrowRight'){e.preventDefault();move(1)}
  if(e.key==='ArrowLeft'){e.preventDefault();move(-1)}
  if(e.key==='Tab'){
   const focusable=[...lb.querySelectorAll('button,a[href]')].filter(x=>x.getClientRects().length);
   const first=focusable[0],last=focusable[focusable.length-1];
   if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}
   else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
  }
 });
 lb.addEventListener('touchstart',e=>{if(e.touches.length===1)touchStart={x:e.touches[0].clientX,y:e.touches[0].clientY}},{passive:true});
 lb.addEventListener('touchend',e=>{if(!touchStart||!lb.classList.contains('open'))return;const dx=e.changedTouches[0].clientX-touchStart.x,dy=e.changedTouches[0].clientY-touchStart.y;touchStart=null;if(Math.abs(dx)>65&&Math.abs(dx)>Math.abs(dy)*1.4)move(dx<0?1:-1)},{passive:true});
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
