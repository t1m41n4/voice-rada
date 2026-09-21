'use client';

import {useEffect,useRef} from 'react';

type Marker={
 id:string;
 latitude?:number;
 longitude?:number;
 public_reference:string;
 risk_level:string;
 verification_status:string;
 category:string;
};

const KENYA_BOUNDS:[[number,number],[number,number]]=[[33.9,-4.7],[41.9,5.5]];

function featureCollection(incidents:Marker[]){
 return {
  type:'FeatureCollection' as const,
  features:incidents.flatMap(incident=>incident.latitude==null||incident.longitude==null?[]:[{
   type:'Feature' as const,
   geometry:{type:'Point' as const,coordinates:[incident.longitude,incident.latitude]},
   properties:{id:incident.id,public_reference:incident.public_reference,risk_level:incident.risk_level,verification_status:incident.verification_status,category:incident.category},
  }]),
 };
}

export function MapPanel({incidents,onSelect}:{incidents:Marker[];onSelect:(id:string)=>void}){
 const target=useRef<HTMLDivElement>(null);
 const mapRef=useRef<any>(null);
 const onSelectRef=useRef(onSelect);
 const incidentsRef=useRef(incidents);
 const token=process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN;
 const mappedCount=incidents.filter(incident=>incident.latitude!=null&&incident.longitude!=null).length;

 useEffect(()=>{onSelectRef.current=onSelect;},[onSelect]);
 useEffect(()=>{incidentsRef.current=incidents;const source=mapRef.current?.getSource('incidents');source?.setData(featureCollection(incidents));},[incidents]);

 useEffect(()=>{
  if(!token||!target.current)return;
  let map:any;let active=true;let pulseTimer:number|undefined;
  (async()=>{
   const mapboxgl=(await import('mapbox-gl')).default;
   if(!active||!target.current)return;
   mapboxgl.accessToken=token;
   map=new mapboxgl.Map({container:target.current,style:'mapbox://styles/mapbox/dark-v11',center:[37.9062,0.0236],zoom:6,maxBounds:KENYA_BOUNDS,attributionControl:false});
   mapRef.current=map;
   map.once('load',()=>{
    if(!active)return;
    map.addSource('incidents',{type:'geojson',data:featureCollection(incidentsRef.current)});
    const critical=['in',['get','risk_level'],['literal',['SEVERE','CRITICAL']]];
    const unverified=['==',['get','verification_status'],'UNVERIFIED'];
    map.addLayer({id:'incident-pulse',type:'circle',source:'incidents',filter:['all',critical,unverified],paint:{'circle-radius':14,'circle-color':'#fb7185','circle-opacity':.12,'circle-stroke-color':'#fb7185','circle-stroke-width':2,'circle-stroke-opacity':.9}});
    map.addLayer({id:'incident-unverified',type:'circle',source:'incidents',filter:unverified,paint:{'circle-radius':['case',critical,10,7],'circle-color':'#f43f5e','circle-stroke-color':'#fecdd3','circle-stroke-width':2,'circle-opacity':.95}});
    map.addLayer({id:'incident-verified',type:'circle',source:'incidents',filter:['!=',['get','verification_status'],'UNVERIFIED'],paint:{'circle-radius':['case',critical,10,7],'circle-color':'#14b8a6','circle-stroke-color':'#ccfbf1','circle-stroke-width':2,'circle-opacity':.98}});
    map.addLayer({id:'incident-verified-check',type:'symbol',source:'incidents',filter:['!=',['get','verification_status'],'UNVERIFIED'],layout:{'text-field':'✓','text-size':12,'text-allow-overlap':true},paint:{'text-color':'#042f2e'}});
    const openIncident=(event:any)=>{const id=event.features?.[0]?.properties?.id;if(id)onSelectRef.current(id);};
    for(const layer of ['incident-unverified','incident-verified','incident-verified-check']){
     map.on('click',layer,openIncident);
     map.on('mouseenter',layer,()=>{map.getCanvas().style.cursor='pointer';});
     map.on('mouseleave',layer,()=>{map.getCanvas().style.cursor='';});
    }
    let expanded=false;
    pulseTimer=window.setInterval(()=>{
     if(!map.getLayer('incident-pulse'))return;
     expanded=!expanded;
     map.setPaintProperty('incident-pulse','circle-radius',expanded?20:14);
     map.setPaintProperty('incident-pulse','circle-opacity',expanded ? 0.03 : 0.15);
    },780);
   });
  })();
  return()=>{active=false;if(pulseTimer)window.clearInterval(pulseTimer);mapRef.current=null;map?.remove();};
 },[token]);

 if(!token)return <div className="mapbox fallback"><span>Tactical map standby</span><p>Add the public Mapbox token to activate responder-only spatial markers.</p></div>;
 return <div><div ref={target} className="mapbox tactical-map"/><p className="map-coverage">{mappedCount} mapped · {incidents.length-mappedCount} location unresolved</p></div>;
}
