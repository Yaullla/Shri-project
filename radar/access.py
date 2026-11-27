"""Local workspace access gates. Not a multi-tenant authentication system."""
import os
import secrets
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials

basic = HTTPBasic(auto_error=False)


def gate(role, request, credentials):
    password = os.environ.get(f"RADAR_{role.upper()}_PASSWORD", "")
    if len(password) < 16:
        raise HTTPException(503, f"Configure RADAR_{role.upper()}_PASSWORD (16+ characters)")
    if (credentials is None
            or not secrets.compare_digest(credentials.username.encode(), role.encode())
            or not secrets.compare_digest(credentials.password.encode(), password.encode())):
        raise HTTPException(401, "Authentication required",
                            headers={"WWW-Authenticate": f'Basic realm="Radar {role}"'})
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        expected = urlsplit(str(request.base_url))
        if request.headers.get("sec-fetch-site") == "cross-site":
            raise HTTPException(403, "Cross-site write forbidden")
        if origin and origin != f"{expected.scheme}://{expected.netloc}":
            raise HTTPException(403, "Cross-origin write forbidden")


def admin(request: Request, credentials: Annotated[HTTPBasicCredentials | None, Depends(basic)]):
    gate("admin", request, credentials)


def traveler(request: Request, credentials: Annotated[HTTPBasicCredentials | None, Depends(basic)]):
    gate("traveler", request, credentials)
