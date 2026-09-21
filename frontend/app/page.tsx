'use client';

import Link from 'next/link';
import {FormEvent,useEffect,useRef,useState} from 'react';
import {AudioRecorder} from './audio-recorder';
import {pendingReports,queueReport,removeQueuedReport} from './offline-queue';

const api=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8001';
const CATEGORIES=['El Niño / Flood Emergency','Goon Activity & Intimidation','Electoral Tension','Resource Dispute'] as const;
type Category=typeof CATEGORIES[number];

export default function Home(){
 const formTarget=useRef<HTMLElement>(null);
 const [text,setText]=useState('');
 const [audio,setAudio]=useState<Blob|null>(null);
 const [location,setLocation]=useState('');
 const [category,setCategory]=useState<Category>('El Niño / Flood Emergency');
 const [notice,setNotice]=useState('');
 const [recorderKey,setRecorderKey]=useState(0);

 async function syncQueue(){
  if(!navigator.onLine)return;
  for(const item of await pendingReports()){
   try{
    const response=await fetch(`${api}/api/v1/reports/text`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(item)});
    if(response.ok)await removeQueuedReport(item.id);
   }catch{/* Keep the private local queue intact until connectivity returns. */}
  }
 }
 useEffect(()=>{syncQueue();addEventListener('online',syncQueue);return()=>removeEventListener('online',syncQueue);},[]);

 async function submit(event:FormEvent){
  event.preventDefault();
  const declaredText=text.trim()?`[Reporter selected domain: ${category}]\n${text.trim()}`:'';
  const body={text:declaredText,location_name:location.trim(),source_type:'PWA' as const};
  try{
   if(!navigator.onLine||(!declaredText&&!audio))throw Error('offline');
   let response:Response;
   if(audio){
    const form=new FormData();
    form.set('audio',audio,'voice-report.webm');form.set('location_name',location.trim());form.set('source_type','PWA');
    response=await fetch(`${api}/api/v1/reports/audio`,{method:'POST',body:form});
   }else response=await fetch(`${api}/api/v1/reports/text`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
   if(!response.ok)throw Error('request failed');
   setNotice('Report received. It is now queued for confidential provider processing.');
  }catch{
   if(!audio&&declaredText)await queueReport(body);
   setNotice(audio?'Voice upload could not be sent. Please reconnect and record again.':'You are offline. This text report is stored only in your device queue and will retry when online.');
  }
  // Clear all locally held report data after every send attempt, including GPS.
  setText('');setAudio(null);setLocation('');setRecorderKey(key=>key+1);
 }
 function useMyLocation(){
  if(!navigator.geolocation){setNotice('Browser location is not available on this device.');return;}
  navigator.geolocation.getCurrentPosition(
   ({coords})=>{setLocation(`${coords.latitude.toFixed(5)}, ${coords.longitude.toFixed(5)}`);setNotice('Approximate location captured. You may edit or remove it before sending.');},
   ()=>setNotice('Location was not shared. You can type a place instead.'),
   {enableHighAccuracy:false,timeout:10000,maximumAge:300000},
  );
 }
 function focusReport(){formTarget.current?.scrollIntoView({behavior:'smooth',block:'center'});}

 return <main className="min-h-screen overflow-x-hidden bg-slate-950 text-slate-100">
  <div className="ambient-glow ambient-glow-one"/><div className="ambient-glow ambient-glow-two"/>
  <header className="site-header">
   <Link href="/" className="brand" aria-label="VoiceRada home"><span className="brand-mark">VR</span><span><b>VoiceRada</b><small>Kenya early warning network</small></span></Link>
   <div className="hidden items-center gap-3 lg:flex"><span className="security-pill"><i/>Zero-Knowledge Privacy Engine Active</span><Link href="/dashboard" className="button-secondary">Responder dashboard</Link></div>
  </header>

  <section className="hero-shell">
   <div className="hero-copy">
    <p className="eyebrow">Confidential community early warning · Kenya</p>
    <h1>Report safely. Help responders see what needs attention.</h1>
    <p className="hero-lead">VoiceRada helps communities share climate-disaster and conflict observations anonymously. Every report remains unverified until neutral responders review it.</p>
    <div className="channel-row" aria-label="Available reporting channels"><span>Web PWA</span><span>USSD <b>*384*55#</b></span><span>WhatsApp</span><span>Voice IVR</span></div>
    <div className="hero-actions"><button className="button-primary" onClick={focusReport}>Report anonymously</button><Link href="/dashboard" className="button-secondary">Responder sign in</Link></div>
   </div>
   <aside className="trust-panel glass-panel">
    <span className="trust-icon" aria-hidden="true">⌁</span>
    <div><p className="eyebrow">Privacy by design</p><h2>Share the event, not your identity.</h2></div>
    <ul><li>No public names or phone numbers.</li><li>Audio is processed transiently, never retained.</li><li>Location is optional and always editable.</li></ul>
   </aside>
  </section>

  <section ref={formTarget} className="report-shell glass-panel" aria-labelledby="report-heading">
   <div className="report-heading"><div><p className="eyebrow">Anonymous report</p><h2 id="report-heading">What did you observe?</h2><p>Choose the closest domain to help responders triage quickly. This does not verify the report.</p></div><span className="secure-label">Encrypted in transit</span></div>
   <form onSubmit={submit} className="report-form">
    <fieldset><legend>Choose a report domain</legend><div className="category-chips">{CATEGORIES.map(item=><button type="button" key={item} className={`category-chip ${category===item?'is-selected':''}`} aria-pressed={category===item} onClick={()=>setCategory(item)}>{item}</button>)}</div></fieldset>
    <label htmlFor="report-text">Describe what you saw or heard <span>(no names needed)</span><textarea id="report-text" value={text} onChange={event=>setText(event.target.value)} placeholder="Maji imeingia kwa nyumba kadhaa karibu na mto..." maxLength={5000} required={!audio}/></label>
    <AudioRecorder key={recorderKey} onReady={setAudio}/>
    <div className="location-grid"><label htmlFor="report-location">Location <span>(optional)</span><input id="report-location" value={location} onChange={event=>setLocation(event.target.value)} placeholder="e.g. Baringo County or a nearby landmark" maxLength={200}/></label><button type="button" className="button-secondary location-button" onClick={useMyLocation}>Use approximate location</button></div>
    <div className="submit-row"><button className="button-primary submit-button" type="submit">Send anonymous report <span aria-hidden="true">→</span></button><p>Do not submit information that could put you or another person at risk.</p></div>
   </form>
  </section>

  <section className="trust-grid" aria-label="VoiceRada reporting safeguards">
   <article><span>01</span><h2>Anonymous by default</h2><p>Public reporting does not require an account. Phone identifiers from supported channels are pseudonymized.</p></article>
   <article><span>02</span><h2>Human verification</h2><p>Automated triage only prioritizes reported observations. Responders must verify before acting on an incident.</p></article>
   <article><span>03</span><h2>Works in the field</h2><p>Use the PWA, USSD, WhatsApp, or IVR. Text reports queue locally if your connection drops.</p></article>
  </section>

  {notice&&<div className="submission-toast" role="status" aria-live="polite"><span aria-hidden="true">✓</span>{notice}</div>}
  <div className="mobile-action-drawer sm:hidden"><span>Need to report something?</span><button className="button-primary" onClick={focusReport}>Report now</button></div>
 </main>;
}
