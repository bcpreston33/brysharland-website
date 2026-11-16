(()=>{
 let entries=[];const fetchEntries=async()=>{if(entries.length)return entries;try{const r=await fetch('assets/news.json',{cache:'no-store'});if(r.ok)entries=await r.json()}catch(e){}return entries};
 const external=x=>typeof x.link==='string'&&/^https?:\/\//i.test(x.link)?x.link:null;
 const direct=x=>x.click_behavior==='external'&&external(x);
 const dialog=document.createElement('div');dialog.className='bry-news-modal';dialog.hidden=true;dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');dialog.setAttribute('aria-label','News announcement');
 dialog.innerHTML='<div class="bry-news-modal-panel"><button type="button" class="bry-news-modal-close" aria-label="Close announcement">×</button><div class="bry-news-modal-body"></div></div>';document.body.append(dialog);
 let restore=null;function close(){dialog.hidden=true;document.body.classList.remove('bry-news-modal-open');if(restore&&restore.isConnected)restore.focus()}
 dialog.querySelector('.bry-news-modal-close').addEventListener('click',close);dialog.addEventListener('click',e=>{if(e.target===dialog)close()});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!dialog.hidden)close()});
 const safeImg=x=>typeof x==='string'&&/^\/?assets\/uploads\/[^?#]+$/i.test(x)?'/'+x.replace(/^\/+/, ''):null;
 function open(x,trigger){restore=trigger;const body=dialog.querySelector('.bry-news-modal-body');body.replaceChildren();
 const meta=document.createElement('div');meta.className='bry-news-modal-meta';meta.textContent=(x.category||'Update')+(x.published_on?' · '+x.published_on:'');body.append(meta);
 const img=safeImg(x.image);if(img){const el=document.createElement('img');el.className='bry-news-modal-image';el.src=img;el.alt=x.title||'Announcement image';body.append(el)}
 const h=document.createElement('h2');h.textContent=x.title||'';body.append(h);
 const desc=document.createElement('div');desc.className='bry-news-modal-copy';desc.textContent=x.full_text||x.description||'';body.append(desc);
 if(external(x)){const a=document.createElement('a');a.className='bry-news-modal-link';a.href=external(x);a.target='_blank';a.rel='noopener noreferrer';a.textContent=x.category==='Press / Media'?'READ ARTICLE ↗':'VISIT LINK ↗';body.append(a)}
 dialog.hidden=false;document.body.classList.add('bry-news-modal-open');dialog.querySelector('.bry-news-modal-close').focus();}
 window.BryNews={open,direct,external,fetchEntries};
 document.addEventListener('click',async e=>{const trigger=e.target.closest('[data-bry-news-index]');if(!trigger)return;const idx=Number(trigger.dataset.bryNewsIndex);const all=await fetchEntries();const x=all[idx];if(!x)return;if(direct(x)){e.preventDefault();window.open(external(x),'_blank','noopener,noreferrer');return}e.preventDefault();open(x,trigger)});
})();