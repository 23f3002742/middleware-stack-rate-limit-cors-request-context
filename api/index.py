from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from mangum import Mangum
import uuid
import time
from collections import defaultdict

app = FastAPI()


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        allowed_origins = ["https://app-cq9cj0.example.com"]
        is_allowed = origin in allowed_origins
        if request.method == "OPTIONS":
            if is_allowed:
                return Response(
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Methods": "GET, OPTIONS",
                        "Access-Control-Allow-Headers": "X-Request-ID, X-Client-Id, Content-Type",
                        "Vary": "Origin",
                    },
                )
            else:
                return Response(status_code=200, headers={"Vary": "Origin"})
        response = await call_next(request)
        if is_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        return response


rate_limit_store = defaultdict(list)
WINDOW_SIZE = 10
MAX_REQUESTS = 12


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_id = request.headers.get("X-Client-Id", "anonymous")
        current_time = time.time()
        rate_limit_store[client_id] = [
            t for t in rate_limit_store[client_id] if current_time - t < WINDOW_SIZE
        ]
        if len(rate_limit_store[client_id]) >= MAX_REQUESTS:
            return Response(
                status_code=429, content="Too Many Requests", media_type="text/plain"
            )
        rate_limit_store[client_id].append(current_time)
        return await call_next(request)


app.add_middleware(RequestContextMiddleware)
app.add_middleware(CustomCORSMiddleware)
app.add_middleware(RateLimitMiddleware)


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "23f3002742@ds.study.iitm.ac.in",
        "request_id": request.state.request_id,
    }


handler = Mangum(app)
