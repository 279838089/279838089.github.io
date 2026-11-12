'use strict';
(function () {
  const $ = (id) => document.getElementById(id);
  const KEY = 'mandiao-radio-v1';
  const MIN = 87.5, MAX = 108, STEP = 12;
  const BUILTIN = [
    {id:'sz-fy971',name:'深圳飞扬音乐',subtitle:'音乐 · 深圳',freq:97.1,genre:'音乐',city:'深圳',urls:['https://satellitepull.cnr.cn/live/wxszfy971/playlist.m3u8','https://ls.qingting.fm/live/1271.m3u8']},
    {id:'sz-sh942',name:'深圳生活广播',subtitle:'生活 · 深圳',freq:94.2,genre:'生活',city:'深圳',urls:['https://satellitepull.cnr.cn/live/wxszsjcgb/playlist.m3u8','https://ls.qingting.fm/live/1273.m3u8']},
    {id:'sz-xf898',name:'深圳先锋新闻',subtitle:'新闻 · 深圳',freq:89.8,genre:'新闻',city:'深圳',urls:['https://ls.qingting.fm/live/1270.m3u8']},
    {id:'sz-kl1062',name:'深圳快乐交通',subtitle:'交通 · 深圳',freq:106.2,genre:'交通',city:'深圳',urls:['https://ls.qingting.fm/live/1272.m3u8']}
  ];
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (_) {}
  const state = {
    custom:Array.isArray(saved.custom) ? saved.custom.filter(validStation).slice(0,100) : [],
    favorites:new Set(Array.isArray(saved.favorites) ? saved.favorites : []),
    volume:Math.max(0,Math.min(1,Number.isFinite(saved.volume)?saved.volume:.8)),
    freq:typeof saved.freq === 'number' ? clamp(saved.freq) : 97.1,
    current:null, tab:'featured', results:[], searching:false,
    status:'idle', wantsPlay:false, sourceIndex:0, session:0, hls:null,
    sleepEnd:0, sleepTimer:null, toastTimer:null, searchToken:0,
    preferredId:saved.lastId || 'sz-fy971'
  };
  const audio = $('radioAudio');
  audio.volume = state.volume;
  $('volume').value = Math.round(state.volume * 100);
  $('volumeValue').textContent = Math.round(state.volume * 100) + '%';
  $('volume').style.setProperty('--vol',Math.round(state.volume*100)+'%');
  const ticks = [];
  for (let i=0;i<=205;i++){
    const f=87.5+i/10;
    const x=i*STEP, major=i%10===5, middle=i%5===0;
    const tick=document.createElement('i');tick.className='tick'+(major?' major':middle?' mid':'');tick.style.left=x+'px';$('tunerRail').appendChild(tick);
    if(major){const label=document.createElement('span');label.className='tick-label';label.style.left=x+'px';label.textContent=String(Math.round(f));$('tunerRail').appendChild(label);}
  }
  function clamp(f){return Math.max(MIN,Math.min(MAX,Math.round(f*10)/10));}
  function validStation(s){return s && typeof s.name==='string' && Array.isArray(s.urls) && s.urls.some(isSecureUrl);}
  function isSecureUrl(u){try{const a=new URL(u);return a.protocol==='https:';}catch(_){return false;}}
  function save(){try{localStorage.setItem(KEY,JSON.stringify({custom:state.custom,favorites:[...state.favorites],volume:state.volume,freq:state.freq,lastId:state.current?.id||state.preferredId}));}catch(_){}}
  function stations(){return [...BUILTIN,...state.custom];}
  function freqString(f){return f==null?'NET':Number(f).toFixed(1);}
  function encode(s){return String(s||'').replace(/[&<>"']/g,(c)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  function uiMessage(s){$('toast').textContent=s;$('toast').classList.add('show');clearTimeout(state.toastTimer);state.toastTimer=setTimeout(()=>$('toast').classList.remove('show'),3200);}
  function setStatus(status, message){
    state.status=status;
    const map={idle:'READY TO TUNE',loading:'CONNECTING...',playing:'ON AIR · LIVE',paused:'PAUSED',error:'SIGNAL LOST'};
    $('onAirText').textContent=message||map[status]||map.idle;
    document.querySelector('.radio-housing').classList.toggle('is-playing',status==='playing');
    const isPlay=status==='playing'||status==='loading';
    $('mainPlayIcon').firstElementChild.setAttribute('href',isPlay?'#icon-pause':'#icon-play');
    $('playPause').setAttribute('aria-label',isPlay?'暂停':'播放');
    $('playCaption').textContent=status==='loading'?'TUNING IN...':isPlay?'PRESS TO PAUSE':'PRESS TO PLAY';
  }
  function displayFrequency(f, isNet){
    $('frequency').textContent=freqString(isNet?null:f);
    $('frequencyBand').textContent=isNet?'INTERNET RADIO':'FM BAND';
    if(!isNet && f!=null){$('tunerRail').style.transform='translate3d('+(-(clamp(f)-MIN)*STEP*10)+'px,0,0)';}
    $('tuner').setAttribute('aria-valuenow',String(f==null?state.freq:clamp(f)));
    $('tuner').setAttribute('aria-valuetext',isNet?'网络电台':freqString(f)+' 兆赫');
  }
  function displayStation(s){
    if(!s){
      $('stationName').textContent='等待发现频道';$('stationSubtitle').textContent='滑动刻度，或者从下方选择电台';
      $('stationMonogram').innerHTML='--<span>FM</span>';
    } else {
      $('stationName').textContent=s.name;
      $('stationSubtitle').textContent=s.subtitle||[s.genre,s.city].filter(Boolean).join(' · ')||'网络直播';
      const big=s.freq?String(Math.floor(s.freq)):'♪';
      $('stationMonogram').innerHTML=encode(big)+'<span>'+(s.freq?'FM':'NET')+'</span>';
    }
  }
  function updateMediaSession(s){
    if(!('mediaSession' in navigator)||!s)return;
    try{
      navigator.mediaSession.metadata=new MediaMetadata({title:s.name,artist:s.subtitle||'慢调 FM · 实时广播',album:'慢调 FM',artwork:[{src:new URL('./icon.png',location.href).href,sizes:'128x128',type:'image/png'}]});
      navigator.mediaSession.setActionHandler('play',()=>{start();});
      navigator.mediaSession.setActionHandler('pause',()=>{pause();});
      navigator.mediaSession.setActionHandler('nexttrack',()=>{stepStation(1);});
      navigator.mediaSession.setActionHandler('previoustrack',()=>{stepStation(-1);});
    }catch(_){}
  }
  function cleanStream(){if(state.hls){try{state.hls.destroy();}catch(_){}state.hls=null;}audio.pause();audio.removeAttribute('src');audio.load();}
  function pause(){
    state.wantsPlay=false;audio.pause();setStatus(state.current?'paused':'idle');
    if('mediaSession' in navigator)try{navigator.mediaSession.playbackState='paused';}catch(_){}
  }
  let hlsPromise=null;
  function loadHls(){
    if(window.Hls)return Promise.resolve(window.Hls);
    if(hlsPromise)return hlsPromise;
    hlsPromise=new Promise((resolve,reject)=>{
      const script=document.createElement('script');script.src='https://cdn.jsdelivr.net/npm/hls.js@1.6.15/dist/hls.min.js';
      script.onload=()=>window.Hls?resolve(window.Hls):reject(new Error('HLS 不可用'));
      script.onerror=()=>reject(new Error('HLS 播放组件加载失败'));
      document.head.appendChild(script);
    }).catch((e)=>{hlsPromise=null;throw e;});
    return hlsPromise;
  }
  function onStreamFailure(token, message){
    if(token!==state.session||!state.wantsPlay)return;
    const s=state.current;
    if(s&&state.sourceIndex+1<s.urls.length){
      state.sourceIndex+=1;uiMessage('切换备用信号源…');connect(token);
    }else{
      state.wantsPlay=false;cleanStream();setStatus('error');uiMessage(message||'该直播源暂时不可用，可更换电台或添加其他源');
    }
  }
  async function connect(token){
    const s=state.current, idx=state.sourceIndex;
    if(!s||token!==state.session||!state.wantsPlay)return;
    const url=s.urls[idx];
    cleanStream();setStatus('loading');
    const timeout=setTimeout(()=>onStreamFailure(token,'连接超时，请更换电台'),14000);
    function settled(){clearTimeout(timeout);}
    const oldFailure=state.fail;state.fail=(reason)=>{settled();onStreamFailure(token,reason);};
    try{
      const isHls=/\.m3u8(?:[?#]|$)/i.test(url);
      const nativeHls=!!audio.canPlayType('application/vnd.apple.mpegurl')||!!audio.canPlayType('application/x-mpegURL');
      if(isHls&&!nativeHls){
        const Hls=await loadHls();
        if(token!==state.session||!state.wantsPlay){settled();return;}
        if(!Hls.isSupported())throw new Error('当前浏览器不支持 HLS');
        state.hls=new Hls({enableWorker:true,lowLatencyMode:false,backBufferLength:0,maxBufferLength:18});
        state.hls.on(Hls.Events.ERROR,(_,data)=>{if(data.fatal&&token===state.session){state.fail('流媒体解码或网络失败');}});
        state.hls.attachMedia(audio);state.hls.loadSource(url);
      }else audio.src=url;
      audio.volume=state.volume;
      audio.play().then(()=>{settled();if(token===state.session&&state.wantsPlay)setStatus('playing');}).catch(err=>{
        settled();if(token!==state.session||!state.wantsPlay)return;
        if(err.name==='NotAllowedError'){state.wantsPlay=false;setStatus('paused');uiMessage('请轻触播放按钮开始收听');}
        else state.fail('播放失败：'+(err.message||'请检查网络'));
      });
    }catch(err){settled();if(token===state.session)state.fail(err.message||'播放失败');}
  }
  function start(){
    if(!state.current){uiMessage('请先选择一个电台');return;}
    if(state.wantsPlay&&state.status==='loading')return;
    if(state.status==='paused'&&audio.src){state.wantsPlay=true;setStatus('loading');audio.play().then(()=>setStatus('playing')).catch(()=>{state.wantsPlay=false;setStatus('error');uiMessage('请再次点击播放，或更换信号源');});return;}
    state.wantsPlay=true;state.sourceIndex=0;const token=++state.session;connect(token);
  }
  function selectStation(s, autoplay){
    state.current=s;state.preferredId=s.id;state.session++;state.wantsPlay=false;cleanStream();setStatus(s?'paused':'idle');
    if(s&&s.freq!=null)state.freq=clamp(s.freq);
    displayFrequency(s&&s.freq!=null?s.freq:state.freq,!!(s&&s.freq==null));
    displayStation(s);updateMediaSession(s);save();renderList();
    if(autoplay&&s)start();
  }
  function stepStation(delta){
    const list=stations().filter(s=>s.freq!=null).sort((a,b)=>a.freq-b.freq);
    if(!list.length)return;
    const index=list.findIndex(s=>s.id===state.current?.id);
    const next=list[(index+delta+list.length)%list.length]||list[0];
    selectStation(next,true);
  }
  function nearest(f){return stations().find(s=>s.freq!=null&&Math.abs(s.freq-f)<.051)||null;}
  function tune(f, commit){
    const value=clamp(f);state.freq=value;
    displayFrequency(value,false);
    if(!commit)return;
    const found=nearest(value);
    if(found){if(state.current?.id!==found.id)selectStation(found,true);else{displayStation(found);save();}}
    else{
      state.current=null;state.session++;state.wantsPlay=false;cleanStream();displayStation(null);setStatus('idle','NO STATION FOUND');save();renderList();
    }
  }
  const tuner=$('tuner');
  let drag=null,raf=0,pendingFreq=state.freq;
  function applyPreview(){raf=0;tune(pendingFreq,false);}
  function preview(f){pendingFreq=clamp(f);if(!raf)raf=requestAnimationFrame(applyPreview);}
  tuner.addEventListener('pointerdown',(e)=>{
    if(e.button!==0&&e.pointerType==='mouse')return;
    drag={x:e.clientX,original:state.freq,moved:false};
    tuner.setPointerCapture(e.pointerId);tuner.classList.add('is-dragging');
  });
  tuner.addEventListener('pointermove',(e)=>{
    if(!drag)return;
    const dx=e.clientX-drag.x;
    if(Math.abs(dx)>3)drag.moved=true;
    preview(drag.original-dx/(STEP*10));
  });
  function endDrag(e){
    if(!drag)return;
    const d=drag;drag=null;tuner.classList.remove('is-dragging');
    if(raf){cancelAnimationFrame(raf);raf=0;}
    let f=pendingFreq;
    if(!d.moved){
      const rect=tuner.getBoundingClientRect();
      f=state.freq+(e.clientX-(rect.left+rect.width/2))/(STEP*10);
    }
    tune(f,true);
  }
  tuner.addEventListener('pointerup',endDrag);
  tuner.addEventListener('pointercancel',()=>{if(!drag)return;drag=null;tuner.classList.remove('is-dragging');tune(state.freq,true);});
  tuner.addEventListener('keydown',(e)=>{const step=e.shiftKey?1:.1;let next=state.freq;
    if(e.key==='ArrowRight'||e.key==='ArrowUp')next+=step;
    else if(e.key==='ArrowLeft'||e.key==='ArrowDown')next-=step;
    else if(e.key==='Home')next=MIN;else if(e.key==='End')next=MAX;else return;
    e.preventDefault();tune(next,true);
  });
  function renderList(){
    let items=state.tab==='featured'?stations():state.tab==='favorites'?
       [...stations(),...state.results].filter(s=>state.favorites.has(s.id)):state.results;
    const unique=new Map(items.map(s=>[s.id,s]));items=[...unique.values()];
    const list=$('stationList');
    if(!items.length){
      let main=state.tab==='favorites'?'这里还没有收藏':'还没有找到电台';
      let detail=state.tab==='favorites'?'点击频道卡片右上角的爱心，收藏喜欢的声音。':state.searching?'正在查找全球电台…':'搜索城市、电台名称或音乐类型，开始探索。';
      list.innerHTML='<div class="empty-state"><b>'+main+'</b><span>'+detail+'</span></div>';
    }else{
      list.innerHTML=items.map(s=>{
        const selected=state.current?.id===s.id, fav=state.favorites.has(s.id);
        return '<article class="station-card'+(selected?' selected':'')+'" role="button" tabindex="0" data-id="'+encode(s.id)+'" aria-label="收听 '+encode(s.name)+'">'+
          '<div class="card-top"><span class="card-type">'+(s.freq!=null?'FM '+freqString(s.freq):'INTERNET RADIO')+'</span>'+
          '<button class="favorite-button'+(fav?' active':'')+'" aria-label="'+(fav?'取消收藏':'收藏')+' '+encode(s.name)+'" data-fav="'+encode(s.id)+'"><svg><use href="#icon-heart"/></svg></button></div>'+
          '<strong>'+encode(s.name)+'</strong><span class="card-description">'+encode(s.subtitle||[s.genre,s.city].filter(Boolean).join(' · ')||'网络直播')+'</span>'+
          '<div class="card-bottom"><span>'+(selected?'● CURRENTLY TUNED':s.custom?'个人添加':s.city||'LIVE RADIO')+'</span><span class="card-arrow">↗</span></div></article>';
      }).join('');
    }
    $('listCount').textContent=items.length+' STATIONS '+(state.tab==='favorites'?'SAVED':'AVAILABLE');
  }
  $('stationList').addEventListener('click',(e)=>{
    const fav=e.target.closest('[data-fav]');
    if(fav){const id=fav.dataset.fav;if(state.favorites.has(id))state.favorites.delete(id);else state.favorites.add(id);save();renderList();return;}
    const card=e.target.closest('[data-id]');if(card){const s=[...stations(),...state.results].find(s=>s.id===card.dataset.id);if(s)selectStation(s,true);}
  });
  $('stationList').addEventListener('keydown',(e)=>{if(e.target.matches('[data-id]')&&(e.key==='Enter'||e.key===' ')){e.preventDefault();e.target.click();}});
  $('playPause').addEventListener('click',()=>{state.wantsPlay?pause():start();});
  $('previous').addEventListener('click',()=>stepStation(-1));
  $('next').addEventListener('click',()=>stepStation(1));
  $('volume').addEventListener('input',(e)=>{state.volume=Number(e.target.value)/100;audio.volume=state.volume;$('volumeValue').textContent=e.target.value+'%';$('volume').style.setProperty('--vol',e.target.value+'%');save();});
  audio.addEventListener('playing',()=>{if(state.wantsPlay){setStatus('playing');if('mediaSession' in navigator)try{navigator.mediaSession.playbackState='playing';}catch(_){}}});
  audio.addEventListener('waiting',()=>{if(state.wantsPlay)setStatus('loading');});
  audio.addEventListener('error',()=>{if(state.wantsPlay&&state.fail)state.fail('音频信号中断');});
  audio.addEventListener('ended',()=>{if(state.wantsPlay&&state.fail)state.fail('电台已停止推流');});
  document.querySelectorAll('[data-tab]').forEach(btn=>btn.addEventListener('click',()=>{
    state.tab=btn.dataset.tab;
    document.querySelectorAll('[data-tab]').forEach(b=>{b.classList.toggle('active',b===btn);b.setAttribute('aria-selected',b===btn?'true':'false');});
    $('exploreTools').hidden=state.tab!=='explore';
    renderList();
    if(state.tab==='explore'&&!state.results.length)searchGlobal('中国');
  }));
  let searchDebounce;
  $('search').addEventListener('input',(e)=>{clearTimeout(searchDebounce);searchDebounce=setTimeout(()=>searchGlobal(e.target.value.trim()),390);});
  $('search').addEventListener('keydown',(e)=>{if(e.key==='Enter'){clearTimeout(searchDebounce);searchGlobal(e.target.value.trim());e.target.blur();}});
  document.querySelectorAll('[data-query]').forEach(b=>b.addEventListener('click',()=>{$('search').value=b.dataset.query;searchGlobal(b.dataset.query);}));
  function parseFreq(name){
    const m=String(name).match(/(?:FM\s*|调频\s*)(8[7-9]|9\d|10[0-8])(?:[.．](\d))?/i);
    if(!m)return null;const f=Number(m[1]+'.'+(m[2]||0));return f>=MIN&&f<=MAX?f:null;
  }
  async function searchGlobal(query){
    state.searchToken++;const token=state.searchToken;
    if(!query){state.results=[];state.searching=false;renderList();return;}
    state.searching=true;state.results=[];renderList();
    const endpoints=['https://de1.api.radio-browser.info','https://at1.api.radio-browser.info','https://nl1.api.radio-browser.info'];
    const params=new URLSearchParams({name:query,hidebroken:'true',order:'votes',reverse:'true',limit:'48'});
    for(const host of endpoints){
      const abort=new AbortController(), timeout=setTimeout(()=>abort.abort(),7500);
      try{
        const resp=await fetch(host+'/json/stations/search?'+params,{signal:abort.signal,headers:{'Accept':'application/json'}});
        if(!resp.ok)throw Error('HTTP '+resp.status);
        const data=await resp.json();clearTimeout(timeout);
        if(token!==state.searchToken)return;
        state.results=(Array.isArray(data)?data:[]).filter(s=>isSecureUrl(s.url_resolved||s.url)).map(s=>({
          id:'rb-'+String(s.stationuuid),name:String(s.name||'未知电台').trim().slice(0,70),
          subtitle:[s.country,s.tags?.split(',')[0]].filter(Boolean).join(' · '),
          genre:s.tags?.split(',')[0]||'广播',city:s.country||'全球',
          freq:parseFreq(s.name),urls:[s.url_resolved||s.url],isRemote:true
        })).filter(s=>s.name&&s.id!=='rb-undefined').slice(0,40);
        state.searching=false;renderList();
        if(!state.results.length)uiMessage('没有匹配的可用 HTTPS 电台，试试其他关键词');
        return;
      }catch(_){clearTimeout(timeout);}
    }
    if(token===state.searchToken){state.searching=false;renderList();uiMessage('全球电台目录暂时无法连接，请稍后再试');}
  }
  $('sleepButton').addEventListener('click',()=>{
    const minutes=state.sleepEnd>0?Math.ceil((state.sleepEnd-Date.now())/60000):0;
    const choices=[0,15,30,60];const index=choices.findIndex(v=>v>=minutes);
    const next=choices[((index<0?3:index)+1)%choices.length];
    if(state.sleepTimer)clearInterval(state.sleepTimer);
    if(!next){state.sleepEnd=0;$('sleepLabel').textContent='睡眠定时';uiMessage('已关闭睡眠定时');return;}
    state.sleepEnd=Date.now()+next*60000;uiMessage(next+' 分钟后自动停止播放');
    function tick(){let left=Math.ceil((state.sleepEnd-Date.now())/60000);if(left<=0){clearInterval(state.sleepTimer);state.sleepTimer=null;state.sleepEnd=0;pause();$('sleepLabel').textContent='睡眠定时';uiMessage('晚安，收音机已自动关闭');}else $('sleepLabel').textContent=left+' 分钟后';}
    tick();state.sleepTimer=setInterval(tick,15000);
  });
  const dialog=$('addDialog');
  function openDialog(){dialog.showModal();$('addError').textContent='';}
  $('openAdd').addEventListener('click',openDialog);$('addBottom').addEventListener('click',openDialog);
  dialog.querySelector('.close-dialog').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',(e)=>{if(e.target===dialog)dialog.close();});
  function importM3u(text){
    const lines=text.split(/\r?\n/), result=[];let name='';
    for(const line0 of lines){const line=line0.trim();if(line.startsWith('#EXTINF')){name=line.split(',').slice(1).join(',').trim();}
      else if(isSecureUrl(line)){result.push({id:'custom-'+Date.now()+'-'+result.length,name:name||'自定义电台 '+(result.length+1),subtitle:'导入播放列表',freq:null,genre:'自定义',city:'个人',custom:true,urls:[line]});name='';}
    }return result;
  }
  $('addForm').addEventListener('submit',(e)=>{
    e.preventDefault();const raw=$('customUrl').value.trim(), name=$('customName').value.trim(), ftext=$('customFreq').value.trim(), f=ftext?Number(ftext):null;
    let added=[];
    if(raw.includes('\n')||raw.startsWith('#EXTM3U')||raw.startsWith('#EXTINF'))added=importM3u(raw).slice(0,50);
    else if(isSecureUrl(raw))added=[{id:'custom-'+Date.now(),name:name||'我的电台',subtitle:'我的收藏 · 自定义源',freq:f,genre:'自定义',city:'个人',custom:true,urls:[raw]}];
    if(!added.length){$('addError').textContent='请输入有效的 HTTPS 音频直播地址，或粘贴 M3U 列表';return;}
    if(f!==null&&(!Number.isFinite(f)||f<MIN||f>MAX||Math.abs(f*10-Math.round(f*10))>.001)){$('addError').textContent='频率请填写 87.5～108.0，精确到 0.1 MHz';return;}
    const count=Math.min(added.length,100-state.custom.length);
    if(count<=0){$('addError').textContent='自定义电台最多保存 100 个';return;}
    state.custom.push(...added.slice(0,count));state.favorites.add(added[0].id);save();renderList();dialog.close();$('addForm').reset();uiMessage('已添加 '+count+' 个自定义电台');
    selectStation(added[0],false);
  });
  const first=stations().find(s=>s.id===state.preferredId)||BUILTIN[0];
  state.current=first;
  if(first.freq!=null)state.freq=first.freq;
  displayFrequency(first.freq!=null?first.freq:state.freq,first.freq==null);displayStation(first);setStatus('paused');renderList();updateMediaSession(first);
  if('serviceWorker' in navigator&&location.protocol==='https:')window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(()=>{}));
})();
