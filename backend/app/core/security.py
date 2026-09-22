import time
from collections import defaultdict,deque
from fastapi import HTTPException,Request

class InMemoryRateLimiter:
    def __init__(self,limit:int=30,window_seconds:int=60):
        self.limit=limit;self.window_seconds=window_seconds;self.requests:dict[str,deque[float]]=defaultdict(deque)
    def check(self,key:str):
        now=time.monotonic();bucket=self.requests[key]
        while bucket and bucket[0]<=now-self.window_seconds:bucket.popleft()
        if len(bucket)>=self.limit:raise HTTPException(429,'Too many requests; please try again shortly.')
        bucket.append(now)

public_limiter=InMemoryRateLimiter()
login_limiter=InMemoryRateLimiter(limit=5,window_seconds=60)
def limit_public_request(request:Request):
    public_limiter.check(request.client.host if request.client else 'unknown')

def limit_login_attempt(request:Request):
    login_limiter.check(request.client.host if request.client else 'unknown')
