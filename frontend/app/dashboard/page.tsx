'use client';

import Link from 'next/link';
import {FormEvent,useCallback,useEffect,useRef,useState} from 'react';
import {MapPanel} from '../map-panel';

const api=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8001';
const CATEGORIES=['El Niño / Flood Emergency','Goon Activity & Intimidation','Electoral Tension','Resource Dispute'] as const;
type VerificationEvent={status:string;reviewer_reference:string;notes?:string;created_at?:string};
type Evidence={evidence_type:string;content_hash:string};
type CorroborationSource={title:string;source:string;published_at:string;url:string};
type WebCorroboration={status:'HIGH'|'MEDIUM'|'UNVERIFIED';summary:string;sources:CorroborationSource[];checked_at:string;availability?:string};
type Incident={id:string;public_reference:string;category:string;source_type:string;location_name?:string;latitude?:number;longitude?:number;risk_level:string;confidence:number;verification_status:string;ai_summary:string;created_at?:string;description?:string;verification_events?:VerificationEvent[];evidence?:Evidence[];web_corroboration?:WebCorroboration};
type Summary={total_reports:number;high_priority:number;unverified:number;verified:number;active_clusters:number};
type Cluster={location_name:string;report_count:number;window_minutes:number};
type ProcessingReport={id:string;source_type:string;location_name?:string;processing_status:'RECEIVED'|'PROCESSING'|'PROCESSED'|'FAILED';processing_error?:string;retryable:boolean};

function HashToken({value}:{value:string}){
 const [hash,setHash]=useState('…');
 useEffect(()=>{let active=true;crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)).then(buffer=>{if(active)setHash(Array.from(new Uint8Array(buffer)).map(part=>part.toString(16).padStart(2,'0')).join('').slice(0,8));}).catch(()=>undefined);return()=>{active=false;};},[value]);
 return <span className="case-hash">Hash: {hash.slice(0,4)}…</span>;
}

function relativeTime(value:string|undefined,now:number){
 if(!value)return 'time unavailable';
 const seconds=Math.max(0,Math.floor((now-new Date(value).getTime())/1000));
 if(seconds<60)return 'just now';
 if(seconds<3600)return `${Math.floor(seconds/60)}m ago`;
 if(seconds<86400)return `${Math.floor(seconds/3600)}h ago`;
 return `${Math.floor(seconds/86400)}d ago`;
}

export default function DashboardPage(){
 const [token,setToken]=useState('');
 const [email,setEmail]=useState('');
 const [password,setPassword]=useState('');
 const [loggingIn,setLoggingIn]=useState(false);
 const [incidents,setIncidents]=useState<Incident[]>([]);
 const [summary,setSummary]=useState<Summary|null>(null);
 const [clusters,setClusters]=useState<Cluster[]>([]);
 const [processing,setProcessing]=useState<ProcessingReport[]>([]);
 const [selected,setSelected]=useState<Incident|null>(null);
 const [rawModalId,setRawModalId]=useState<string|null>(null);
 const [newIncidentIds,setNewIncidentIds]=useState<Set<string>>(()=>new Set());
 const [newIncidentNotice,setNewIncidentNotice]=useState('');
 const [risk,setRisk]=useState('');
 const [status,setStatus]=useState('');
 const [category,setCategory]=useState('');
 const [mobileView,setMobileView]=useState<'map'|'feed'>('feed');
 const [notice,setNotice]=useState('');
 const [clock,setClock]=useState(Date.now());
 const highlightTimers=useRef<number[]>([]);
 const headers=useCallback(()=>({Authorization:`Bearer ${token}`,'Content-Type':'application/json'}),[token]);

 const load=useCallback(async()=>{
  if(!token)return;
  const params=new URLSearchParams({page_size:'100'});
  if(risk)params.set('risk_level',risk);
  if(status)params.set('verification_status',status);
  if(category)params.set('category',category);
  try{
   const [feed,stats,activity,queue]=await Promise.all([
    fetch(`${api}/api/v1/incidents?${params}`,{headers:headers()}),
    fetch(`${api}/api/v1/dashboard/summary`,{headers:headers()}),
    fetch(`${api}/api/v1/dashboard/clusters`,{headers:headers()}),
    fetch(`${api}/api/v1/reports/processing?limit=25`,{headers:headers()}),
   ]);
   if(feed.ok)setIncidents((await feed.json()).items);
   if(stats.ok)setSummary(await stats.json());
   if(activity.ok)setClusters((await activity.json()).clusters);
   if(queue.ok)setProcessing((await queue.json()).items);
  }catch{setNotice('Live data connection is unavailable. Check the API and try again.');}
 },[token,risk,status,category,headers]);

 useEffect(()=>{const timer=window.setInterval(()=>setClock(Date.now()),60_000);return()=>window.clearInterval(timer);},[]);
 useEffect(()=>()=>highlightTimers.current.forEach(timer=>window.clearTimeout(timer)),[]);
 useEffect(()=>{
  if(!token)return;
  void load();
  const socket=new WebSocket(`${api.replace(/^http/,'ws')}/api/v1/events?token=${encodeURIComponent(token)}`);
  socket.onmessage=event=>{
   try{
    const payload=JSON.parse(event.data);
    if(payload.type==='incident.created'){
     const id=String(payload.incident_id);
     setNewIncidentIds(previous=>new Set(previous).add(id));
     setNewIncidentNotice(`New Incident Reported: ${payload.category||'Uncategorised report'}`);
     highlightTimers.current.push(window.setTimeout(()=>setNewIncidentIds(previous=>{const next=new Set(previous);next.delete(id);return next;}),12_000));
    }
   }catch{/* Ignore malformed event payloads; the next event will refresh data. */}
   void load();
  };
  return()=>socket.close();
 },[token,load]);

 async function login(event:FormEvent){
  event.preventDefault();setLoggingIn(true);
  try{
   const response=await fetch(`${api}/api/v1/auth/login`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});
   const data=await response.json();
   if(!response.ok||!data.access_token){setNotice('Login failed. Check your responder email and password.');return;}
   setToken(data.access_token);setPassword('');setNotice('Secure responder session active.');
  }catch{setNotice('Login is unavailable. Check the API connection and try again.');}
  finally{setLoggingIn(false);}
 }
 async function select(id:string){
  const response=await fetch(`${api}/api/v1/incidents/${id}`,{headers:headers()});
  if(response.ok)setSelected(await response.json());else setNotice('This incident detail is no longer available.');
 }
 function openOriginalReport(id:string){setRawModalId(id);void select(id);}
 async function verify(id:string){const response=await fetch(`${api}/api/v1/incidents/${id}/verification`,{method:'PATCH',headers:headers(),body:JSON.stringify({status:'VERIFIED',notes:'Verified during responder review.'})});if(response.ok){setNotice('Incident marked verified.');await select(id);void load();}}
 async function retry(report:ProcessingReport){const response=await fetch(`${api}/api/v1/reports/${report.id}/retry`,{method:'POST',headers:headers()});setNotice(response.ok?'Retry queued for provider processing.':report.processing_error||'This report cannot be retried.');void load();}
 async function logout(){try{await fetch(`${api}/api/v1/auth/logout`,{method:'POST',headers:headers()});}finally{setToken('');setSelected(null);setIncidents([]);setProcessing([]);setSummary(null);setNewIncidentIds(new Set());setNotice('Responder session closed.');}}

 if(!token)return <main className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 sm:px-8"><header className="site-header mb-12"><Link href="/" className="brand"><span className="brand-mark">VR</span><span><b>VoiceRada</b><small>Kenya early warning network</small></span></Link><Link href="/" className="button-secondary">Public reporting</Link></header><section className="login-shell glass-panel"><p className="eyebrow">Restricted responder access</p><h1>Operations center</h1><p>Sign in to view sensitive incident locations, processing states, and verification tools.</p><form onSubmit={login}><label>Email<input type="email" autoComplete="email" value={email} onChange={event=>setEmail(event.target.value)} required/></label><label>Password<input type="password" autoComplete="current-password" value={password} onChange={event=>setPassword(event.target.value)} required/></label><button className="button-primary submit-button" disabled={loggingIn}>{loggingIn?'Signing in…':'Sign in securely'}</button></form>{notice&&<p className="form-notice" role="status">{notice}</p>}</section></main>;

 const activeReports=processing.filter(report=>report.processing_status!=='PROCESSED');
 const dashboardContent=<>
  <section className="tactical-map-panel"><div className="panel-title"><div><p className="eyebrow">Spatial map view</p><h2>Live incident geography</h2></div><span className="live-indicator"><i/>Live</span></div><MapPanel incidents={incidents} onSelect={select}/><p className="map-caption">Pulsing red markers indicate unverified severe or critical reports. Solid teal markers with a check are human verified.</p></section>
  <section className="tactical-feed-panel"><div className="panel-title"><div><p className="eyebrow">Incident feed</p><h2>Responder triage queue</h2></div><span>{incidents.length} visible</span></div><div className="filter-grid"><select aria-label="Filter by category" value={category} onChange={event=>setCategory(event.target.value)}><option value="">All domains</option>{CATEGORIES.map(item=><option key={item}>{item}</option>)}</select><select aria-label="Filter by severity" value={risk} onChange={event=>setRisk(event.target.value)}><option value="">All severity</option><option>CRITICAL</option><option>SEVERE</option><option>HIGH</option><option>MODERATE</option><option>LOW</option></select><select aria-label="Filter by verification status" value={status} onChange={event=>setStatus(event.target.value)}><option value="">All verification</option><option>UNVERIFIED</option><option>VERIFIED</option><option>NEEDS_REVIEW</option></select></div><div className="incident-scroll">{incidents.map(incident=><article className={`tactical-incident ${newIncidentIds.has(incident.id)?'is-new-incident':''}`} key={incident.id} onClick={()=>void select(incident.id)}><div className="incident-topline"><span className={`risk-badge risk-${incident.risk_level}`}>{incident.risk_level}</span><span className="verify-badge">{incident.verification_status.replace('_',' ')}</span><span className="relative-time">{relativeTime(incident.created_at,clock)}</span></div><h3>{incident.category}</h3><p>{incident.ai_summary}</p><div className="incident-meta"><HashToken value={incident.id}/><span>{incident.location_name||'Location unresolved'}</span><span>{Math.round(incident.confidence*100)}% confidence</span></div><div className="incident-actions"><button className="original-report-action" onClick={event=>{event.stopPropagation();openOriginalReport(incident.id);}}>View original report</button>{incident.verification_status==='UNVERIFIED'&&<button className="verify-action" onClick={event=>{event.stopPropagation();void verify(incident.id);}}>Verify report</button>}</div></article>)}{!incidents.length&&<p className="empty-state">No incidents match the active filters.</p>}</div></section>
 </>;

 const originalReport=rawModalId&&selected?.id===rawModalId?selected:null;
 return <main className="tactical-shell min-h-screen bg-slate-950 text-slate-100"><header className="tactical-header"><Link href="/" className="brand"><span className="brand-mark">VR</span><span><b>VoiceRada</b><small>Responder operations center</small></span></Link><div className="header-status"><span className="security-pill"><i/>Responder session secured</span><button className="button-secondary" onClick={logout}>Sign out</button></div></header><section className="tactical-heading"><div><p className="eyebrow">Neutral humanitarian responder view</p><h1>Early warning operations center</h1></div><p>Prioritize reported needs, preserve uncertainty, and record human verification.</p></section>{summary&&<section className="kpi-grid"><article><span>Total reports</span><b>{summary.total_reports}</b><small>all processed incidents</small></article><article className="kpi-critical"><span>Critical alerts</span><b>{summary.high_priority}</b><small>high-priority reports</small></article><article><span>Unverified alerts</span><b>{summary.unverified}</b><small>require human review</small></article><article><span>Verified incident clusters</span><b>{summary.active_clusters}</b><small>emerging activity areas</small></article></section>}<div className="mobile-tabs lg:hidden" role="tablist"><button role="tab" aria-selected={mobileView==='feed'} className={mobileView==='feed'?'is-active':''} onClick={()=>setMobileView('feed')}>Incident feed</button><button role="tab" aria-selected={mobileView==='map'} className={mobileView==='map'?'is-active':''} onClick={()=>setMobileView('map')}>Spatial map</button></div><section className={`tactical-workspace mobile-${mobileView}`}>{dashboardContent}</section>{clusters.length>0&&<section className="cluster-bar"><strong>Emerging reporting activity</strong>{clusters.map(cluster=><span key={cluster.location_name}>{cluster.report_count} reports near {cluster.location_name} in {cluster.window_minutes} minutes</span>)}</section>}{activeReports.length>0&&<section className="processing-strip"><strong>Processing monitor</strong>{activeReports.map(report=><article key={report.id}><span className={`processing-status processing-${report.processing_status}`}>{report.processing_status}</span><span>{report.source_type} · {report.location_name||'Location not supplied'}</span>{report.retryable&&<button onClick={()=>void retry(report)}>Retry</button>}</article>)}</section>}{selected&&<section className="triage-drawer" aria-label="Selected incident detail"><button className="drawer-close" onClick={()=>setSelected(null)} aria-label="Close incident detail">×</button><p className="eyebrow">{selected.verification_status==='VERIFIED'?'Human verified':'Unverified report'}</p><h2>{selected.category}</h2><p>{selected.ai_summary}</p><div className="drawer-meta"><span>{selected.public_reference}</span><HashToken value={selected.id}/><span>{selected.location_name||'Location unresolved'}</span></div><section className="corroboration-panel"><h3>Recent web corroboration</h3>{selected.web_corroboration?<><span className={`corroboration-badge corroboration-${selected.web_corroboration.status}`}>{selected.web_corroboration.status} signal</span><p>{selected.web_corroboration.summary}</p>{selected.web_corroboration.sources.length?<ul>{selected.web_corroboration.sources.map(source=><li key={source.url}><a href={source.url} target="_blank" rel="noreferrer">{source.source}</a> · {relativeTime(source.published_at,clock)}<br/><span>{source.title}</span></li>)}</ul>:<p className="muted-detail">No qualifying source published within the last 48 hours.</p>}</>:<p className="muted-detail">Corroboration check is pending.</p>}</section><h3>Evidence</h3>{selected.evidence?.length?<ul>{selected.evidence.map(evidence=><li key={evidence.content_hash}>{evidence.evidence_type} · hash recorded; private audio not exposed</li>)}</ul>:<p>No retained evidence.</p>}<h3>Verification timeline</h3>{selected.verification_events?.length?<ul>{selected.verification_events.map((event,index)=><li key={index}>{event.status} by {event.reviewer_reference}{event.notes&&` — ${event.notes}`}</li>)}</ul>:<p>No human review recorded.</p>}</section>}{originalReport&&<div className="original-report-backdrop" role="presentation" onMouseDown={()=>setRawModalId(null)}><section className="original-report-modal" role="dialog" aria-modal="true" aria-labelledby="original-report-title" onMouseDown={event=>event.stopPropagation()}><button className="drawer-close" onClick={()=>setRawModalId(null)} aria-label="Close original report">×</button><p className="eyebrow">Responder-only source record</p><h2 id="original-report-title">Original report</h2><div className="original-report-meta"><span>{originalReport.public_reference}</span><span>Channel: {originalReport.source_type}</span><span>{relativeTime(originalReport.created_at,clock)}</span></div><pre>{originalReport.description||'Original text is unavailable.'}</pre><p className="muted-detail">This is the unedited submission. It remains an unverified report unless a responder has recorded verification.</p></section></div>}{newIncidentNotice&&<div className="new-incident-toast" role="status" aria-live="polite"><span className="live-dot"/> {newIncidentNotice}</div>}{notice&&<div className="submission-toast" role="status">{notice}</div>}</main>;
}
