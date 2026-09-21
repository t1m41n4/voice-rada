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

const KENYA_CAMERA_BOUNDS:[[number,number],[number,number]]=[[33.90982,-4.67690],[41.89908,5.50600]];
const KENYA_MAX_BOUNDS:[[number,number],[number,number]]=KENYA_CAMERA_BOUNDS;
const KENYA_FIT_OPTIONS={padding:{top:20,bottom:20,left:20,right:20},duration:0};

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
  const mapTarget=target.current;
  if(!token||!mapTarget)return;
  let map:any;let active=true;let pulseTimer:number|undefined;let resizeObserver:ResizeObserver|undefined;let cameraIsFramed=false;let lastWidth=0;let lastHeight=0;
  (async()=>{
   const mapboxgl=(await import('mapbox-gl')).default;
   if(!active)return;
   mapboxgl.accessToken=token;
   map=new mapboxgl.Map({container:mapTarget,style:'mapbox://styles/mapbox/dark-v11',bounds:KENYA_CAMERA_BOUNDS,fitBoundsOptions:KENYA_FIT_OPTIONS,maxBounds:KENYA_MAX_BOUNDS,renderWorldCopies:false,attributionControl:false});
   mapRef.current=map;
   map.once('load',()=>{
    if(!active)return;
    const frameKenya=()=>{
     const width=mapTarget.clientWidth;const height=mapTarget.clientHeight;
     if(width===0||height===0)return;
     map.resize();
     const camera=map.cameraForBounds(KENYA_CAMERA_BOUNDS,KENYA_FIT_OPTIONS);
     if(!camera)return;
     map.setMinZoom(0);
     if(!cameraIsFramed||width!==lastWidth||height!==lastHeight){
      map.jumpTo({center:camera.center,zoom:camera.zoom,bearing:0,pitch:0});
      cameraIsFramed=true;lastWidth=width;lastHeight=height;
     }
     // Kenya is the widest permitted view; responders can still zoom in and back out to this frame.
     map.setMinZoom(camera.zoom);
    };
    resizeObserver=new ResizeObserver(()=>requestAnimationFrame(frameKenya));
    resizeObserver.observe(mapTarget);
    requestAnimationFrame(frameKenya);
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
  return()=>{active=false;resizeObserver?.disconnect();if(pulseTimer)window.clearInterval(pulseTimer);mapRef.current=null;map?.remove();};
 },[token]);

 if(!token)return <div className="mapbox fallback"><span>Tactical map standby</span><p>Add the public Mapbox token to activate responder-only spatial markers.</p></div>;
 return <div className="map-panel"><div ref={target} className="mapbox tactical-map"/><p className="map-coverage">{mappedCount} mapped · {incidents.length-mappedCount} location unresolved</p></div>;
}
