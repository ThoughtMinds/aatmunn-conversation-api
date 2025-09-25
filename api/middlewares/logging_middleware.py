import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from api.core.logging_config import logger, request_id_var


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for logging HTTP requests.

    This middleware logs incoming requests and outgoing responses, including
    the request ID, method, path, status code, and duration.
    Handles streaming responses properly without buffering.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process and log a request and its response.

        This method generates a unique request ID, logs the incoming request,
        awaits the response, and then logs the response details.

        Args:
            request (Request): The incoming HTTP request.
            call_next (function): The next middleware or endpoint in the chain.

        Returns:
            Response: The HTTP response.
        """
        request_id = uuid.uuid4().hex
        request_id_var.set(request_id)

        start_time = time.time()

        if request.url.path != "/":  # ignore health checks
            logger.debug(
                {
                    "event": "request_received",
                    "method": request.method,
                    "path": request.url.path,
                    "request_id": request_id,
                }
            )

        response = await call_next(request)
        duration = time.time() - start_time

        # For streaming responses, log immediately without waiting for completion
        if isinstance(response, StreamingResponse):
            logger.debug(
                {
                    "event": "streaming_response_started",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": round(duration, 4),
                    "request_id": request_id,
                    "response_type": "streaming",
                },
                extra={"bold": True},
            )
            return response

        # For regular responses, log completion details
        if request.url.path != "/":  # ignore health checks
            logger.debug(
                {
                    "event": "request_completed",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": round(duration, 4),
                    "request_id": request_id,
                    "response_type": "regular",
                }
            )

        return response
