'use client';
import {useEffect,useState} from 'react';
import {pendingReportCount} from './offline-queue';
export function QueueStatus(){const [count,setCount]=useState(0),[online,setOnline]=useState(true);useEffect(()=>{const refresh=async()=>{setOnline(navigator.onLine);setCount(await pendingReportCount())};refresh();addEventListener('online',refresh);addEventListener('offline',refresh);const timer=setInterval(refresh,3000);return()=>{removeEventListener('online',refresh);removeEventListener('offline',refresh);clearInterval(timer)}},[]);if(!count&&online)return null;return <p className="queue-status">{count?`${count} text report${count===1?' is':'s are'} pending delivery.`:'You are offline. New text reports will be queued.'}</p>}
