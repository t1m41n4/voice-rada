'use client';

import {useRef,useState} from 'react';

export function AudioRecorder({onReady}:{onReady:(audio:Blob|null)=>void}){
 const recorder=useRef<MediaRecorder|null>(null);
 const chunks=useRef<Blob[]>([]);
 const [recording,setRecording]=useState(false);
 const [ready,setReady]=useState(false);
 const [message,setMessage]=useState('');

 async function start(){
  try{
   const stream=await navigator.mediaDevices.getUserMedia({audio:true});
   chunks.current=[];
   const media=new MediaRecorder(stream);
   recorder.current=media;
   media.ondataavailable=event=>chunks.current.push(event.data);
   media.onstop=()=>{
    stream.getTracks().forEach(track=>track.stop());
    onReady(new Blob(chunks.current,{type:media.mimeType||'audio/webm'}));
    setReady(true);setRecording(false);setMessage('Voice report ready. You can send it when safe.');
   };
   media.start();setRecording(true);setReady(false);setMessage('Recording in progress. Tap stop when finished.');
  }catch{setMessage('Microphone access was not granted. You can submit a text report instead.');}
 }
 function stop(){recorder.current?.stop();}
 function clear(){onReady(null);setReady(false);setMessage('Voice recording removed.');}

 return <section className={`recording-widget ${recording?'is-recording':''}`} aria-label="Voice report recorder">
  <div className="waveform" aria-hidden="true">{[0,1,2,3,4,5,6].map(bar=><i key={bar} style={{animationDelay:`${bar*0.08}s`}} />)}</div>
  <div className="flex-1">
   <strong>{recording?'Listening securely':'Tap to record a voice report'}</strong>
   <p>{recording?'Audio is processed transiently and is not retained.':'You can stop, review your choice, or use text instead.'}</p>
  </div>
  <button type="button" className={`record-button ${recording?'record-button-stop':''}`} onClick={recording?stop:start} aria-pressed={recording}>
   <span aria-hidden="true">{recording?'■':'●'}</span>{recording?'Stop':'Record'}
  </button>
  {ready&&<button type="button" className="button-secondary min-touch" onClick={clear}>Remove</button>}
  <small className="recording-message" aria-live="polite">{message}</small>
 </section>;
}
