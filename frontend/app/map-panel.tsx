'use client';

import {useEffect,useRef} from 'react';

type Marker={id:string;latitude?:number;longitude?:number;public_reference:string;risk_level:string};

export function MapPanel({incidents,onSelect}:{incidents:Marker[];onSelect:(id:string)=>void}){
 const target=useRef<HTMLDivElement>(null);
 const token=process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN;

 useEffect(()=>{
  if(!token||!target.current)return;
  let map:any;let markers:any[]=[];let active=true;
  (async()=>{
   const mapboxgl=(await import('mapbox-gl')).default;
   if(!active||!target.current)return;
   mapboxgl.accessToken=token;
   map=new mapboxgl.Map({container:target.current,style:'mapbox://styles/mapbox/dark-v11',center:[36.8172,-1.2864],zoom:5,attributionControl:false});
   for(const incident of incidents){
    if(incident.latitude==null||incident.longitude==null)continue;
    const critical=['SEVERE','CRITICAL'].includes(incident.risk_level);
    const element=document.createElement('button');
    element.type='button';element.className=`tactical-marker ${critical?'tactical-marker-critical':''}`;
    element.setAttribute('aria-label',`Open ${incident.public_reference}`);
    element.onclick=()=>onSelect(incident.id);
    const marker=new mapboxgl.Marker({element}).setLngLat([incident.longitude,incident.latitude]).setPopup(new mapboxgl.Popup({closeButton:false}).setText(incident.public_reference));
    marker.addTo(map);markers.push(marker);
   }
  })();
  return()=>{active=false;markers.forEach(marker=>marker.remove());map?.remove();};
 },[incidents,token,onSelect]);

 if(!token)return <div className="mapbox fallback"><span>Tactical map standby</span><p>Add the public Mapbox token to activate responder-only spatial markers.</p></div>;
 return <div ref={target} className="mapbox tactical-map"/>;
}
