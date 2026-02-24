"""
Audit middleware: publishes HTTP request metadata to RabbitMQ after
each response so every API call is traceable.
Skips health-check and static-file paths to avoid noise.
"""
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

from ..core.rabbitmq import mq, get_client_ip

logger = logging.getLogger(__name__)

# Paths we don't want to flood the audit queue with
_SKIP_PATHS = {"/health", "/", "/uploads", "/docs", "/redoc", "/openapi.json"}


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000)

        path = request.url.path
        if not any(path.startswith(skip) for skip in _SKIP_PATHS):
            try:
                await mq.publish_security_event(
                    event="http_request",
                    method=request.method,
                    path=path,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                    ip_address=get_client_ip(request),
                )
            except Exception as exc:
                logger.debug("AuditMiddleware publish error: %s", exc)

        return response
