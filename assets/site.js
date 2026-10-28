// Artwork is published from Pages CMS into content/artwork and compiled to assets/artwork.json.
(async function(){
  let data=[];
  try {const r=await fetch('assets/artwork.json',{cache:'no-store'});if(!r.ok)throw Error('No artwork manifest');data=await r.json();}catch(e){return;}
  const escapeText=s=>String(s??'');
  const slug=document.body.dataset.category;
  if(slug){
    const gallery=document.querySelector('.gallery');
    const art=data.filter(x=>x.category===slug && x.image);
    if(gallery){gallery.replaceChildren();
      if(!art.length){const empty=document.createElement('p');empty.className='gallery-empty';empty.textContent='Artwork will appear here as it is added.';gallery.append(empty)}
      // Stable, varied neon color per artwork (does not change on refresh).
      const palette=['#ff29b4','#08e8f4','#ff851a','#f5f323','#a435ff'];
      art.forEach((x,index)=>{const b=document.createElement('button');
        const seed=String(x.title||'')+'|'+String(x.image||'');
        let hash=2166136261;
        for(let j=0;j<seed.length;j++){hash=Math.imul(hash^seed.charCodeAt(j),16777619)}
        b.style.setProperty('--art-color',palette[((hash>>>0)+index)%palette.length]);b.className='art';b.type='button';b.dataset.full=x.image;b.dataset.title=x.title;b.dataset.year=x.year||'';b.dataset.medium=x.medium||'';b.dataset.dimensions=x.dimensions||'';b.dataset.description=x.description||'';
        const im=document.createElement('img');im.src=x.image;im.alt=x.title;im.loading='lazy';
        const info=document.createElement('div');info.className='info';const title=document.createElement('strong');title.textContent=x.title;
        const details=document.createElement('small');details.textContent=[x.medium,x.dimensions,x.year].filter(Boolean).join(' · ');
        info.append(title,details);b.append(im,info);gallery.append(b)});
      if(typeof window.setupArtworkLightbox==='function')window.setupArtworkLightbox();
    }
  }
  const tiles=document.querySelectorAll('.tiles .tile');
  tiles.forEach(tile=>{const cat=tile.getAttribute('href').replace('.html','');const candidate=data.find(x=>x.category===cat && x.featured && x.image)||data.find(x=>x.category===cat && x.image);
    if(candidate){const im=tile.querySelector('.photo img');if(im){im.src=candidate.image;im.alt=candidate.title}}
  });
})();

function setupArtworkLightbox(){
 const lb=document.querySelector('.lightbox');if(!lb)return;
 const items=[...document.querySelectorAll('.gallery [data-full]')];if(!items.length)return;
 let i=0;const large=lb.querySelector('#large'),caption=lb.querySelector('#caption');
 function show(){large.src=items[i].dataset.full;large.alt=items[i].dataset.title;caption.replaceChildren();const title=document.createElement('strong');title.textContent=items[i].dataset.title;caption.append(title);const meta=[items[i].dataset.medium,items[i].dataset.dimensions,items[i].dataset.year].filter(Boolean).join(' · ');if(meta){const detail=document.createElement('span');detail.className='caption-meta';detail.textContent=meta;caption.append(detail)}if(items[i].dataset.description){const desc=document.createElement('span');desc.className='caption-description';desc.textContent=items[i].dataset.description;caption.append(desc)}const count=document.createElement('span');count.className='caption-count';count.textContent=(i+1)+' / '+items.length;caption.append(count)}
 function close(){lb.classList.remove('open');large.removeAttribute('src')}
 items.forEach((el,n)=>el.addEventListener('click',()=>{i=n;show();lb.classList.add('open')}));
 lb.querySelector('.close').onclick=close;
 lb.querySelector('.prev').onclick=()=>{i=(i+items.length-1)%items.length;show()};
 lb.querySelector('.next').onclick=()=>{i=(i+1)%items.length;show()};
 lb.addEventListener('click',e=>{if(e.target===lb)close()});
 document.addEventListener('keydown',e=>{if(!lb.classList.contains('open'))return;if(e.key==='Escape')close();if(e.key==='ArrowRight'){i=(i+1)%items.length;show()}if(e.key==='ArrowLeft'){i=(i+items.length-1)%items.length;show()}})
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
