'use client';
import {useEffect,useRef} from 'react';
type Marker={id:string;latitude?:number;longitude?:number;public_reference:string;risk_level:string};
export function MapPanel({incidents,onSelect}:{incidents:Marker[];onSelect:(id:string)=>void}){
 const target=useRef<HTMLDivElement>(null);const token=process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN;
 useEffect(()=>{if(!token||!target.current)return;let map:any;let markers:any[]=[];let active=true;(async()=>{const mapboxgl=(await import('mapbox-gl')).default;if(!active||!target.current)return;mapboxgl.accessToken=token;map=new mapboxgl.Map({container:target.current,style:'mapbox://styles/mapbox/light-v11',center:[36.8172,-1.2864],zoom:5});for(const incident of incidents){if(incident.latitude==null||incident.longitude==null)continue;const marker=new mapboxgl.Marker({color:incident.risk_level==='SEVERE'||incident.risk_level==='CRITICAL'?'#bd4c42':'#0c6257'}).setLngLat([incident.longitude,incident.latitude]).setPopup(new mapboxgl.Popup().setText(incident.public_reference));marker.getElement().onclick=()=>onSelect(incident.id);marker.addTo(map);markers.push(marker)}})();return()=>{active=false;markers.forEach(marker=>marker.remove());map?.remove()}},[incidents,token,onSelect]);
 if(!token)return <div className="mapbox fallback"><span>MAPBOX TOKEN NOT CONFIGURED</span><p>Map markers will appear here after `NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN` is added.</p></div>;
 return <div ref={target} className="mapbox"/>;
}
