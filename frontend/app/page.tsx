'use client';

import { FormEvent, useEffect, useState } from 'react';
import { AudioRecorder } from './audio-recorder';
import { MapPanel } from './map-panel';
import { pendingReports, queueReport, removeQueuedReport } from './offline-queue';

const api = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
type VerificationEvent = { status: string; reviewer_reference: string; notes?: string };
type Evidence = { evidence_type: string; content_hash: string };
type Incident = { id: string; public_reference: string; category: string; location_name?: string; latitude?: number; longitude?: number; risk_level: string; confidence: number; verification_status: string; ai_summary: string; description?: string; verification_events?: VerificationEvent[]; evidence?: Evidence[] };
type Summary = { total_reports: number; high_priority: number; unverified: number; active_clusters: number };
type Cluster = { location_name: string; report_count: number; window_minutes: number };
type ProcessingReport = { id: string; source_type: string; location_name?: string; processing_status: 'RECEIVED' | 'PROCESSING' | 'PROCESSED' | 'FAILED'; processing_error?: string; retryable: boolean };

export default function Home() {
  const [dashboard, setDashboard] = useState(false);
  const [token, setToken] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loggingIn, setLoggingIn] = useState(false);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [processing, setProcessing] = useState<ProcessingReport[]>([]);
  const [selected, setSelected] = useState<Incident | null>(null);
  const [risk, setRisk] = useState('');
  const [status, setStatus] = useState('');
  const [text, setText] = useState('');
  const [audio, setAudio] = useState<Blob | null>(null);
  const [location, setLocation] = useState('Kibera');
  const [notice, setNotice] = useState('');
  const headers = () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' });

  async function load() {
    if (!token) return;
    const params = new URLSearchParams({ page_size: '100' });
    if (risk) params.set('risk_level', risk);
    if (status) params.set('verification_status', status);
    const [feed, stats, activity, queue] = await Promise.all([
      fetch(`${api}/api/v1/incidents?${params}`, { headers: headers() }),
      fetch(`${api}/api/v1/dashboard/summary`, { headers: headers() }),
      fetch(`${api}/api/v1/dashboard/clusters`, { headers: headers() }),
      fetch(`${api}/api/v1/reports/processing?limit=25`, { headers: headers() }),
    ]);
    if (feed.ok) setIncidents((await feed.json()).items);
    if (stats.ok) setSummary(await stats.json());
    if (activity.ok) setClusters((await activity.json()).clusters);
    if (queue.ok) setProcessing((await queue.json()).items);
  }

  async function select(id: string) {
    const response = await fetch(`${api}/api/v1/incidents/${id}`, { headers: headers() });
    if (response.ok) setSelected(await response.json());
  }
  async function syncQueue() {
    if (!navigator.onLine) return;
    for (const item of await pendingReports()) {
      try {
        const response = await fetch(`${api}/api/v1/reports/text`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(item) });
        if (response.ok) await removeQueuedReport(item.id);
      } catch { /* Keep the report queued for the next online event. */ }
    }
    load();
  }
  useEffect(() => {
    load(); syncQueue(); addEventListener('online', syncQueue);
    if (!token) return () => removeEventListener('online', syncQueue);
    const socket = new WebSocket(`${api.replace(/^http/, 'ws')}/api/v1/events?token=${encodeURIComponent(token)}`);
    socket.onmessage = () => load();
    return () => { removeEventListener('online', syncQueue); socket.close(); };
  }, [token, risk, status]);

  async function login(event: FormEvent) {
    event.preventDefault();
    setLoggingIn(true);
    try {
      const response = await fetch(`${api}/api/v1/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
      const data = await response.json();
      if (!response.ok || !data.access_token) { setNotice('Login failed. Check your responder email and password.'); return; }
      setToken(data.access_token); setPassword(''); setNotice('Responder session active.');
    } catch { setNotice('Login is unavailable. Check the API connection and try again.'); }
    finally { setLoggingIn(false); }
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    const body = { text, location_name: location, source_type: 'PWA' as const };
    try {
      if (!navigator.onLine || (!text && !audio)) throw Error('offline');
      let response: Response;
      if (audio) {
        const form = new FormData(); form.set('audio', audio, 'voice-report.webm'); form.set('location_name', location); form.set('source_type', 'PWA');
        response = await fetch(`${api}/api/v1/reports/audio`, { method: 'POST', body: form });
      } else response = await fetch(`${api}/api/v1/reports/text`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      if (!response.ok) throw Error('request failed');
      setNotice('Report received for provider processing.');
    } catch {
      if (!audio) await queueReport(body);
      setNotice(audio ? 'Voice upload could not be sent. Please reconnect and record again.' : 'You are offline. This text report is stored locally and will retry when online.');
    }
    setText(''); setAudio(null); load();
  }
  async function verify(id: string) {
    await fetch(`${api}/api/v1/incidents/${id}/verification`, { method: 'PATCH', headers: headers(), body: JSON.stringify({ status: 'VERIFIED', notes: 'Verified during responder review.' }) });
    await select(id); load();
  }
  async function retry(report: ProcessingReport) {
    const response = await fetch(`${api}/api/v1/reports/${report.id}/retry`, { method: 'POST', headers: headers() });
    setNotice(response.ok ? 'Retry queued for provider processing.' : report.processing_error || 'This report cannot be retried.');
    load();
  }
  async function logout() {
    try { await fetch(`${api}/api/v1/auth/logout`, { method: 'POST', headers: headers() }); }
    finally { setToken(''); setSelected(null); setIncidents([]); setProcessing([]); setSummary(null); }
  }
  function useMyLocation() {
    if (!navigator.geolocation) { setNotice('Browser location is not available on this device.'); return; }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => { setLocation(`${coords.latitude.toFixed(5)}, ${coords.longitude.toFixed(5)}`); setNotice('Approximate location captured. You can edit it before sending.'); },
      () => setNotice('Location was not shared. You can type a place instead.'),
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
    );
  }

  if (!dashboard) return <main className="landing"><header><div><b>VoiceRada</b><small>Community early warning - Kenya</small></div><button onClick={() => setDashboard(true)}>Responder login</button></header><section className="hero"><p>PRIVACY-FIRST COMMUNITY REPORTING</p><h1>See emerging needs. Verify before acting.</h1><span>VoiceRada helps communities share unverified observations and helps neutral responders prioritize human review.</span><div><button onClick={() => setDashboard(true)}>Submit a report</button><button className="secondary" onClick={() => setDashboard(true)}>Responder dashboard</button></div></section><section className="landinggrid"><div><h2>Report your observation</h2><p>Use web, WhatsApp, USSD, or IVR. Share only what you can safely report.</p></div><div><h2>Privacy matters</h2><p>Phone identifiers are pseudonymous. Audio is processed in memory and never made public.</p></div><div><h2>Human review required</h2><p>Reports and automated triage are not facts or official emergency classifications.</p></div></section></main>;

  const activeReports = processing.filter((report) => report.processing_status !== 'PROCESSED');
  return <main><header><div><b>VoiceRada</b><small>Community early warning - Kenya</small></div>{token ? <button onClick={logout}>Sign out</button> : <button onClick={() => setDashboard(true)}>Responder login</button>}</header><section className="intro"><p>Operational dashboard</p><h1>Reports need review, not assumptions.</h1><span>Automated triage helps prioritize unverified observations. It is not an official emergency classification.</span></section>{!token && <section className="card login-card"><h2>Responder login</h2><p>Demo access is available for evaluation.</p><form onSubmit={login}><label>Email<input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label><label>Password<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label><button disabled={loggingIn}>{loggingIn ? 'Signing in…' : 'Sign in to dashboard'}</button></form></section>}{token && summary && <section className="metrics"><div><b>{summary.total_reports}</b><span>Total reports</span></div><div><b>{summary.high_priority}</b><span>High priority</span></div><div><b>{summary.unverified}</b><span>Unverified</span></div><div><b>{summary.active_clusters}</b><span>Emerging clusters</span></div></section>}<div className="grid"><section className="card report"><h2>Submit a community report</h2><form onSubmit={submit}><label>What happened?<textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="Maji imeingia kwa nyumba kadhaa karibu na mto..." /></label><AudioRecorder onReady={setAudio} /><label>Location (optional)<input value={location} onChange={(event) => setLocation(event.target.value)} /></label><button type="button" className="secondary" onClick={useMyLocation}>Use my approximate location</button><button>Send report</button></form><p className="notice">{notice}</p></section><section className="card map"><h2>Incident map</h2><MapPanel incidents={incidents} onSelect={select} /><small>Coordinates are sensitive and shown only to authenticated responders.</small></section></div>{token && activeReports.length > 0 && <section className="card processing"><h2>Processing queue</h2>{activeReports.map((report) => <article key={report.id}><div><strong>{report.source_type} report</strong><span className={`status processing-${report.processing_status}`}>{report.processing_status}</span><p>{report.location_name || 'Location not supplied'}{report.processing_error && ` - ${report.processing_error}`}</p></div>{report.retryable && <button onClick={() => retry(report)}>Retry processing</button>}</article>)}</section>}<section className="card feed"><div className="feedhead"><h2>Live incident feed</h2><select value={risk} onChange={(event) => setRisk(event.target.value)}><option value="">All risk levels</option><option>SEVERE</option><option>HIGH</option><option>MODERATE</option><option>LOW</option></select><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All statuses</option><option>UNVERIFIED</option><option>VERIFIED</option><option>NEEDS_REVIEW</option></select></div>{clusters.length > 0 && <aside><b>Emerging reporting activity</b>{clusters.map((cluster) => <span key={cluster.location_name}>{cluster.report_count} reports near {cluster.location_name} in {cluster.window_minutes} minutes - needs verification</span>)}</aside>}{!token ? <p>Log in with the configured responder account to view protected incident data.</p> : incidents.map((incident) => <article key={incident.id} onClick={() => select(incident.id)}><div><strong>{incident.public_reference}</strong><span className={`pill ${incident.risk_level}`}>{incident.risk_level}</span><span className="status">{incident.verification_status}</span><h3>{incident.category.replace('_', ' ')}</h3><p>{incident.ai_summary}</p><small>{incident.location_name || 'Location not resolved'} - confidence {Math.round(incident.confidence * 100)}% - AI-extracted</small></div>{incident.verification_status === 'UNVERIFIED' && <button onClick={(event) => { event.stopPropagation(); verify(incident.id); }}>Mark verified</button>}</article>)}</section>{selected && <section className="card details"><button className="close" onClick={() => setSelected(null)}>Close</button><p className="eyebrow">{selected.verification_status === 'VERIFIED' ? 'HUMAN VERIFIED' : 'UNVERIFIED REPORT'}</p><h2>{selected.public_reference} - {selected.category.replace('_', ' ')}</h2><p>{selected.description}</p><h3>Evidence</h3>{selected.evidence?.length ? <ul>{selected.evidence.map((evidence) => <li key={evidence.content_hash}>{evidence.evidence_type} - hash recorded, private audio not exposed</li>)}</ul> : <p>No retained evidence.</p>}<h3>Verification audit</h3>{selected.verification_events?.length ? <ul>{selected.verification_events.map((event, index) => <li key={index}>{event.status} by {event.reviewer_reference} {event.notes && `- ${event.notes}`}</li>)}</ul> : <p>No human review recorded.</p>}</section>}</main>;
}
