import asyncio
import json
from fastapi import WebSocket

class IncidentEventHub:
    def __init__(self):
        self.connections:set[WebSocket]=set()
        self.loop:asyncio.AbstractEventLoop|None=None
    def attach_loop(self):
        self.loop=asyncio.get_running_loop()
    async def connect(self,websocket:WebSocket):
        await websocket.accept()
        self.connections.add(websocket)
    def disconnect(self,websocket:WebSocket):
        self.connections.discard(websocket)
    async def broadcast(self,event:dict):
        payload=json.dumps(event,default=str)
        stale=[]
        for websocket in self.connections:
            try:await websocket.send_text(payload)
            except Exception:stale.append(websocket)
        for websocket in stale:self.connections.discard(websocket)
    def publish(self,event:dict):
        if self.loop and self.loop.is_running():asyncio.run_coroutine_threadsafe(self.broadcast(event),self.loop)

event_hub=IncidentEventHub()
