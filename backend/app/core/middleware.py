import logging,time,uuid
from starlette.middleware.base import BaseHTTPMiddleware

logger=logging.getLogger('voicerada.requests')
class SafeRequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        request_id=request.headers.get('X-Request-ID') or str(uuid.uuid4())
        started=time.perf_counter();response=await call_next(request)
        response.headers['X-Request-ID']=request_id
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['X-Frame-Options']='DENY'
        logger.info('request_complete request_id=%s route=%s status_code=%s duration_ms=%d',request_id,request.url.path,response.status_code,(time.perf_counter()-started)*1000)
        return response
