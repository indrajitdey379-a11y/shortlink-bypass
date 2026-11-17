
import os
import hmac
import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse

from shortlink_bypass import bypass

app = FastAPI(
    title="INDRAJIT BYPASS API",
    version="1.0.0"
)


def check_url(url: str):
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(400, "Only HTTP/HTTPS URLs are allowed")

    if not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(400, "Invalid URL")

    try:
        addresses = socket.getaddrinfo(
            parsed.hostname, None, type=socket.SOCK_STREAM
        )
        for item in addresses:
            ip = ipaddress.ip_address(item[4][0])
            if not ip.is_global:
                raise HTTPException(400, "Private or local URLs are not allowed")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "Could not validate URL")


def authenticate(authorization: str | None):
    secret = os.getenv("API_SECRET")

    if not secret:
        raise HTTPException(503, "API_SECRET is not configured")

    expected = f"Bearer {secret}"

    if not authorization or not hmac.compare_digest(
        authorization, expected
    ):
        raise HTTPException(401, "Invalid API token")


@app.get("/")
def home():
    return {
        "name": "INDRAJIT BYPASS API",
        "status": "online",
        "version": "1.0.0",
        "endpoint": "/bypass?url=SHORTLINK"
    }


@app.get("/bypass")
def bypass_api(
    url: str = Query(..., min_length=8, max_length=4096),
    authorization: str | None = Header(default=None)
):
    authenticate(authorization)
    check_url(url)

    try:
        result = bypass(url)

        if not result:
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "message": "This shortlink could not be bypassed",
                    "original_url": url
                }
            )

        return {
            "success": True,
            "original_url": url,
            "direct_link": result,
            "message": "Bypassed successfully"
        }

    except HTTPException:
        raise
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal bypass error"
            }
        )
