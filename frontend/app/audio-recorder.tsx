'use client';
import {useRef,useState} from 'react';
export function AudioRecorder({onReady}:{onReady:(audio:Blob|null)=>void}){
 const recorder=useRef<MediaRecorder|null>(null),chunks=useRef<Blob[]>([]);const [recording,setRecording]=useState(false),[ready,setReady]=useState(false),[message,setMessage]=useState('');
 async function start(){try{const stream=await navigator.mediaDevices.getUserMedia({audio:true});chunks.current=[];const media=new MediaRecorder(stream);recorder.current=media;media.ondataavailable=e=>chunks.current.push(e.data);media.onstop=()=>{stream.getTracks().forEach(track=>track.stop());const audio=new Blob(chunks.current,{type:media.mimeType||'audio/webm'});onReady(audio);setReady(true);setRecording(false);setMessage('Voice report ready to submit.')};media.start();setRecording(true);setReady(false);setMessage('Recording…')}catch{setMessage('Microphone access was not granted.')}}
 function stop(){recorder.current?.stop()}function clear(){onReady(null);setReady(false);setMessage('')}
 return <div className="recorder"><button type="button" onClick={recording?stop:start}>{recording?'Stop recording':'Record voice report'}</button>{ready&&<button type="button" className="secondary" onClick={clear}>Remove recording</button>}<small>{message}</small></div>
}
