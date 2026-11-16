
(async()=>{
 const host=document.querySelector('#bry-featured');
 if(!host)return;
 const load=async p=>{const r=await fetch(p,{cache:'no-store'});if(!r.ok)throw Error(p);return r.json()};
 const validDate=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!isNaN(Date.parse(s+'T00:00:00Z'));
 const today=new Date();today.setHours(0,0,0,0);
 const date=s=>new Date(s+'T00:00:00');
 const days=(v,fallback)=>Number.isFinite(Number(v))&&Number(v)>0?Number(v):fallback;
 const safeImage=s=>typeof s==='string'&&/^\/?assets\/uploads\/[^?#]+$/i.test(s)?'/'+s.replace(/^\/+/,''):null;
 const safeLink=s=>typeof s==='string'&&(/^(https?:\/\/)/i.test(s)||/^\/?[a-z0-9/_-]+\.html(?:#[\w-]+)?$/i.test(s))?s:null;
 const text=(el,t)=>{el.textContent=t||'';return el};
 try{
  const [art,news,cfg]=await Promise.all([load('assets/artwork.json'),load('assets/news.json'),load('assets/featured-home.json')]);
  const duration=days(cfg.default_days,30);
  const eligible=items=>items.filter(x=>{
   if(x.feature_override==='hide'||!validDate(x.published_on))return false;
   const start=date(x.published_on);
   if(start>today)return false;
   if(x.feature_override==='pin')return !validDate(x.feature_until)||today<=date(x.feature_until);
   const end=validDate(x.feature_until)?date(x.feature_until):new Date(start.getFullYear(),start.getMonth(),start.getDate()+days(x.feature_days,duration)-1);
   return today<=end;
  }).sort((a,b)=>b.published_on.localeCompare(a.published_on));
  const choose=(items,mode,title)=>{
   if(mode==='hide')return null;
   const candidates=eligible(items);
   if(mode==='pin'&&title)return candidates.find(x=>x.title===title)||null;
   return candidates.find(x=>x.feature_override==='pin')||candidates[0]||null;
  };
  const picks=[['art',choose(art,cfg.art_mode,cfg.art_pin_title)],['news',choose(news,cfg.news_mode,cfg.news_pin_title)]].filter(x=>x[1]);
  for(const [kind,x] of picks){
   const gallery=({queer:'queer.html',portraits:'portraits.html','star-wars':'star-wars.html',various:'various.html'}[x.category]||'index.html#work');
   const link=kind==='art'?(x.image?gallery+'#artwork='+encodeURIComponent(x.image):gallery):safeLink(x.link);
   const img=safeImage(x.image);
   if(kind==='art'&&!img)continue;
   const card=document.createElement('article');card.className='bry-featured-card';card.dataset.kind=kind;
   const media=document.createElement('div');media.className='bry-featured-art';
   if(img){const pic=document.createElement('img');pic.src=img;pic.alt=x.title||'Artwork';pic.loading='lazy';media.append(pic);}else{card.classList.add('bry-featured-no-image');media.textContent=({Star:'★',Calendar:'▣',Newspaper:'▤',Heart:'♥',Sparkles:'✦'})[x.icon]||'✦';}
   const content=document.createElement('div');content.className='bry-featured-content';
   const kicker=document.createElement('div');kicker.className='bry-featured-kicker';text(kicker,kind==='art'?'JUST ADDED':(x.category||'NEWS & UPDATES'));
   const h=document.createElement('h2');text(h,x.title);
   const p=document.createElement('p');
   const description=String(x.description||'').trim();
   if(description&&!/^description goes here\.?$/i.test(description)){text(p,description);content.append(p)}
   content.append(kicker,h,p);if(kind==='news'){
    const a=document.createElement('a');a.href='#news';a.dataset.bryNewsIndex=String(news.indexOf(x));text(a,'READ MORE');content.append(a);
   }else if(link){const a=document.createElement('a');a.href=link;text(a,'VIEW ARTWORK');content.append(a);}card.append(media,content);host.querySelector('.bry-featured-grid').append(card);
  }
  host.hidden=!host.querySelector('.bry-featured-card');
 }catch(e){console.warn('Featured updates unavailable',e);host.hidden=true}
})();
