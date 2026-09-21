'use client';
import {useEffect} from 'react';
export function ServiceWorker(){useEffect(()=>{if(!('serviceWorker'in navigator))return;let refreshed=false;const refreshForNewWorker=()=>{if(!refreshed){refreshed=true;window.location.reload()}};navigator.serviceWorker.addEventListener('controllerchange',refreshForNewWorker);navigator.serviceWorker.register('/sw.js').catch(()=>undefined);return()=>navigator.serviceWorker.removeEventListener('controllerchange',refreshForNewWorker)},[]);return null}
