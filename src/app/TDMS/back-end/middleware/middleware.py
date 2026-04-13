from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Optional
from jose import jwt, JWTError
from config.settings import settings
import logging


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exclude_paths=None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/", "/docs", "/openapi.json", "/redoc", "/favicon.ico"]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        logger = logging.getLogger(__name__)

        # Skip auth for certain paths
        if path in self.exclude_paths or method == "OPTIONS":
            logger.debug("AuthMiddleware: skipped auth for %s %s", method, path)
            response = await call_next(request)
            return response

        # Check for token in Authorization header
        auth_header = request.headers.get("Authorization")
        token = None

        if auth_header and auth_header.startswith("Bearer"):
            token = auth_header[len("Bearer "):]
        else:
            # Special case for dashboard API that might use query param
            if path == "/api/v1/dashboard":
                raw_token = request.query_params.get("token")
                if raw_token and raw_token.startswith("Bearer "):
                    token = raw_token[len("Bearer "):]

        if not token:
            logger.warning(
                "AuthMiddleware: missing token for %s %s (auth_header=%s, query_token=%s)",
                method,
                path,
                bool(auth_header),
                bool(request.query_params.get("token")),
            )
            return JSONResponse({"detail": "Authorization header missing"}, status_code=401)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != "access":
                logger.warning(
                    "AuthMiddleware: invalid token type for %s %s (type=%s, user=%s)",
                    method,
                    path,
                    payload.get("type"),
                    payload.get("user_name"),
                )
                return JSONResponse({"detail": "Invalid token type"}, status_code=401)
            request.state.user = payload
        except JWTError as exc:
            # Best-effort insight without trusting the token.
            try:
                claims = jwt.get_unverified_claims(token)
            except Exception:
                claims = {}
            logger.warning(
                "AuthMiddleware: token decode failed for %s %s (error=%s, type=%s, user=%s, exp=%s)",
                method,
                path,
                exc.__class__.__name__,
                claims.get("type"),
                claims.get("user_name"),
                claims.get("exp"),
            )
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        response = await call_next(request)
        return response
